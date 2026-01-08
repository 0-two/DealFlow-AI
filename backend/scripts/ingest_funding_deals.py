"""
Ingest Funding Deal Data from Company CSV
Converts company funding information into FundingDeal records for Trends analytics
"""

import pandas as pd
import asyncio
import logging
import os
from datetime import datetime
from app.services.vector_store_service import vector_store_service
from app.services.embedding_service import embedding_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FundingDealIngestion:
    """Ingest company funding data into FundingDeal collection"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
        self.deals = []
    
    def load_csv(self):
        """Load and inspect CSV"""
        logger.info(f"Loading CSV from {self.csv_path}")
        
        # Verify file exists
        if not os.path.exists(self.csv_path):
            logger.error(f"❌ CSV file not found: {self.csv_path}")
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        logger.info(f"✅ CSV file exists, size: {os.path.getsize(self.csv_path)} bytes")
        
        self.df = pd.read_csv(self.csv_path, encoding='utf-8')
        
        # Normalize column names (strip whitespace)
        self.df.columns = [c.strip() for c in self.df.columns]
        
        logger.info(f"✅ Loaded {len(self.df)} rows from CSV")
        logger.info(f"📋 Columns: {self.df.columns.tolist()}")
        
        # Show sample
        logger.info("\n📝 Sample data (first 3 rows):")
        for idx, row in self.df.head(3).iterrows():
            logger.info(f"  Row {idx}: {row.get('One Liner Descriptic', 'N/A')} | "
                       f"Stage: {row.get('Funding Status', 'N/A')} | "
                       f"Amount: {row.get('Total Funding', 'N/A')}")
    
    def clean_and_filter(self):
        """
        Clean data and apply filters for funding deals
        """
        logger.info("\n" + "="*60)
        logger.info("Filtering for quality funding deals...")
        logger.info("="*60)
        
        original_count = len(self.df)
        logger.info(f"Starting with {original_count} rows")
        
        # 1. Remove rows with missing critical fields
        before = len(self.df)
        self.df = self.df.dropna(subset=['One Liner'])
        removed = before - len(self.df)
        logger.info(f"✓ Removed {removed} entries with no company name → {len(self.df)} remaining")
        
        # 2. Keep only rows with funding information (stage + amount + date)
        before = len(self.df)
        self.df = self.df[
            (self.df['Funding Status'].notna()) &
            (self.df['Total Funding'].notna()) &
            (self.df['Last Funding'].notna())
        ]
        removed = before - len(self.df)
        logger.info(f"✓ Removed {removed} entries with incomplete funding info → {len(self.df)} remaining")
        
        # 3. Remove 'Redacted' or empty startup names
        before = len(self.df)
        self.df = self.df[
            (self.df['One Liner'].str.strip() != '') &
            (self.df['One Liner'].str.lower() != 'redacted')
        ]
        removed = before - len(self.df)
        logger.info(f"✓ Removed {removed} redacted/empty names → {len(self.df)} remaining")
        
        logger.info(f"\n✅ Final filtered dataset: {len(self.df)} companies with funding deals")
    
    def parse_funding_amount(self, amount_str):
        """
        Parse funding amount string to float (in millions USD)
        Handles formats like: $60,000,000 or 60000000 or 60M
        """
        if pd.isna(amount_str):
            return 0.0
        
        try:
            amount_str = str(amount_str).strip()
            
            # Remove currency symbols and commas
            amount_str = amount_str.replace('$', '').replace(',', '').replace('₹', '')
            
            # Handle M/B suffixes
            if 'M' in amount_str.upper():
                return float(amount_str.upper().replace('M', '')) / 1000000
            elif 'B' in amount_str.upper():
                return float(amount_str.upper().replace('B', '')) / 1000
            
            # Try to convert to float
            amount = float(amount_str)
            
            # If amount > 1000000000, likely in cents, convert to millions
            if amount > 1000000000:
                return amount / 1000000
            # If amount > 1000000, likely in dollars, convert to millions
            elif amount > 1000000:
                return amount / 1000000
            else:
                return amount
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse funding amount: {amount_str}")
            return 0.0
    
    def parse_date(self, date_str):
        """
        Parse date string to RFC3339 format (required by Weaviate)
        Handles: DD-MMM-YY, YYYY-MM-DD, Full Month Name formats, etc.
        """
        if pd.isna(date_str):
            return None
        
        try:
            date_str = str(date_str).strip()
            
            # Try common formats (order matters - try specific formats first)
            formats = [
                '%d-%b-%y',      # 22-Sep-21
                '%d-%b-%Y',      # 22-Sep-2021
                '%B %d, %Y',     # February 7, 2019
                '%B %d %Y',      # February 7 2019
                '%b %d, %Y',     # Feb 7, 2019
                '%b %d %Y',      # Feb 7 2019
                '%Y-%m-%d',      # 2021-09-22
                '%m/%d/%Y',      # 09/22/2021
                '%d/%m/%Y',      # 22/09/2021
                '%d %b %Y',      # 22 Sep 2021
                '%d %B %Y',      # 22 February 2021
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    # Return RFC3339 format with Z suffix (UTC)
                    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date: {date_str}")
            return None
        except Exception as e:
            logger.warning(f"Date parsing error for {date_str}: {e}")
            return None
    
    def normalize_stage(self, stage_str):
        """Normalize funding stage names"""
        if pd.isna(stage_str):
            return "Unknown"
        
        stage = str(stage_str).strip().lower()
        
        # Map variations to standard stages
        stage_mapping = {
            'seed': 'Seed',
            'series a': 'Series A',
            'series b': 'Series B',
            'series c': 'Series C',
            'series d': 'Series D',
            'series e': 'Series E',
            'series f': 'Series F',
            'pre-series a': 'Pre-Series A',
            'growth': 'Growth',
            'private equity': 'Private Equity',
            'ipo': 'IPO',
            'acquired': 'Acquired',
            'merger': 'Merger',
        }
        
        for key, value in stage_mapping.items():
            if key in stage:
                return value
        
        return "Other"
    
    def extract_investors(self, investors_str):
        """Extract investor names from string"""
        if pd.isna(investors_str):
            return []
        
        investors = str(investors_str).split(',')
        investors = [inv.strip() for inv in investors if inv.strip()]
        return investors[:10]  # Limit to 10 investors
    
    def infer_sector(self, description):
        """Infer sector from company description"""
        if pd.isna(description):
            return "Other"
        
        description_lower = str(description).lower()
        
        sector_keywords = {
            'Fintech': ['fintech', 'payment', 'banking', 'crypto', 'blockchain', 'fund', 'wallet'],
            'Edtech': ['education', 'learning', 'edtech', 'course', 'school', 'student'],
            'Healthtech': ['health', 'medical', 'doctor', 'hospital', 'wellness', 'fitness', 'pharma'],
            'E-commerce': ['ecommerce', 'shopping', 'retail', 'marketplace', 'commerce'],
            'SaaS': ['saas', 'software', 'platform', 'tool', 'service', 'cloud'],
            'AI/ML': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural'],
            'Agritech': ['agriculture', 'farming', 'agri', 'crop', 'farm'],
            'Logistics': ['logistics', 'delivery', 'shipping', 'transport', 'supply chain'],
            'Travel': ['travel', 'hotel', 'booking', 'flight', 'tour'],
            'Food': ['food', 'restaurant', 'delivery', 'cafe', 'catering'],
        }
        
        for sector, keywords in sector_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return sector
        
        return "Other"
    
    def transform_to_deals(self):
        """Transform CSV rows into FundingDeal records"""
        logger.info("\n" + "="*60)
        logger.info("Transforming data to FundingDeal records...")
        logger.info("="*60)
        
        self.deals = []
        
        for idx, row in self.df.iterrows():
            try:
                startup_name = str(row.get('One Liner', '')).strip()
                
                # Parse funding details
                amount = self.parse_funding_amount(row.get('Total Funding'))
                date = self.parse_date(row.get('Last Funding'))
                stage = self.normalize_stage(row.get('Funding Status'))
                
                # Skip if critical data missing
                if not startup_name or amount <= 0 or not date:
                    continue
                
                # Extract additional info
                description = row.get('Description', '')
                investors = self.extract_investors(row.get('Investors', ''))
                sector = self.infer_sector(description)
                year_founded = row.get('Year Founded')
                
                deal = {
                    'startup_name': startup_name,
                    'amount': amount,
                    'stage': stage,
                    'date': date,
                    'investors': investors,
                    'sector': sector,
                    'year_founded': year_founded if pd.notna(year_founded) else None,
                    'description': str(description).strip()[:500] if pd.notna(description) else '',
                    'one_liner': str(row.get('One Liner', '')).strip()[:200],
                }
                
                self.deals.append(deal)
            
            except Exception as e:
                logger.warning(f"Error transforming row {idx}: {e}")
                continue
        
        logger.info(f"✅ Transformed {len(self.deals)} funding deals")
        
        # Show sample deals
        if self.deals:
            logger.info("\n📊 Sample deals:")
            for deal in self.deals[:3]:
                logger.info(f"  • {deal['startup_name']} | {deal['stage']} | "
                           f"₹{deal['amount']:.2f} Cr | {deal['date']}")
    
    async def upload_to_weaviate(self):
        """Upload funding deals to Weaviate"""
        logger.info("\n" + "="*60)
        logger.info("Uploading to Weaviate...")
        logger.info("="*60)
        
        if not self.deals:
            logger.warning("No deals to upload")
            return
        
        try:
            # FundingDeal collection is created by VectorStoreService.initialize_collections()
            logger.info("✅ FundingDeal collection ready")
            
            # Prepare documents for batch insertion
            documents = []
            for deal in self.deals:
                # Create content for embedding - ensure it's never empty
                content_parts = [
                    deal['startup_name'],
                    deal['stage'],
                    deal['sector'],
                    deal['description']
                ]
                content = ' '.join(str(p).strip() for p in content_parts if p and str(p).strip())
                
                # Fallback if still empty
                if not content or not content.strip():
                    content = f"{deal['startup_name']} {deal['stage']} funding deal"
                
                doc = {
                    "startup_name": deal['startup_name'],
                    "amount": deal['amount'],
                    "stage": deal['stage'],
                    "date": deal['date'],
                    "investors": deal['investors'],
                    "sector": deal['sector'],
                    "currency": "INR",
                    "content": content,
                    "source": "Company CSV"
                }
                documents.append(doc)
            
            # Upload all documents at once using add_documents
            # The service will generate embeddings automatically
            success = await vector_store_service.add_documents(
                collection_name="FundingDeal",
                documents=documents,
                generate_embeddings=True
            )
            
            if success:
                logger.info(f"\n🎉 Successfully uploaded {len(self.deals)} funding deals!")
            else:
                logger.warning(f"⚠️ Upload completed with issues; check logs for details")
        
        except Exception as e:
            logger.error(f"❌ Weaviate upload error: {e}")
            raise
    
    async def run(self):
        """Run full ingestion pipeline"""
        try:
            self.load_csv()
            self.clean_and_filter()
            self.transform_to_deals()
            await self.upload_to_weaviate()
            logger.info("\n" + "="*60)
            logger.info("✅ Ingestion complete!")
            logger.info("="*60)
        
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}")
            raise


async def main():
    """Main entry point"""
    csv_path = "D:\\AI-Verse Hackathon\\Dataset\\Ramp's Airtable database\\Company Database-Grid view.csv"
    
    ingestion = FundingDealIngestion(csv_path)
    await ingestion.run()


if __name__ == "__main__":
    asyncio.run(main())
