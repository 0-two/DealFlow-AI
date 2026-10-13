"""
Ingest Investor Data from Ramps VC Database CSV
Intelligently filters and structures data for Weaviate
"""

import pandas as pd
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.vector_store_service import vector_store_service
from app.services.embedding_service import embedding_service
import re


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvestorDataIngestion:
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
    
    def load_csv(self):
        """Load and inspect CSV"""
        logger.info(f"Loading CSV from {self.csv_path}")
        
        self.df = pd.read_csv(self.csv_path, encoding='utf-8')
        
        logger.info(f"Loaded {len(self.df)} investors")
        logger.info(f"Columns: {self.df.columns.tolist()}")
        
        # Show sample
        logger.info("\nSample data:")
        logger.info(self.df.head(2))
    
    def clean_and_filter(self):
        """
        Clean data and apply smart filters
        Keep only high-quality, relevant investors
        """
        
        logger.info("\n" + "="*60)
        logger.info("Filtering for quality investors...")
        logger.info("="*60)
        
        original_count = len(self.df)
        
        # 1. Remove rows with missing critical fields
        self.df = self.df.dropna(subset=['Investor Name'])
        logger.info(f"✓ Removed {original_count - len(self.df)} entries with no name")
        
        # 2. Focus on VCs and Angel investors (remove others)
        valid_types = ['VC', 'Angel', 'Venture Capital', 'Angel Investor', 
                       'Micro VC', 'Early Stage VC', 'Seed Fund']
        self.df = self.df[self.df['Fund Type'].str.contains(
            '|'.join(valid_types), 
            case=False, 
            na=False
        )]
        logger.info(f"✓ Kept only VC/Angel investors: {len(self.df)} remaining")
        
        # 3. Prioritize investors with good data quality
        # Has website OR has partner email OR has portfolio
        self.df['quality_score'] = (
            self.df['Website (if available)'].notna().astype(int) +
            self.df['Partner Email'].notna().astype(int) +
            self.df['Portfolio Companies'].notna().astype(int) +
            self.df['Fund Description'].notna().astype(int) +
            (self.df['Number of Investments'].fillna(0) > 0).astype(int)
        )
        
        # Keep investors with quality_score >= 2
        self.df = self.df[self.df['quality_score'] >= 2]
        logger.info(f"✓ Kept high-quality entries: {len(self.df)} remaining")
        
        # 4. Prioritize based on activity
        self.df = self.df.sort_values('Number of Investments', ascending=False, na_position='last')
        
        # 5. Geographic filtering (prioritize but don't exclude)
        # Score India-based higher but keep international
        self.df['india_based'] = self.df['Location'].str.contains(
            'India|Bangalore|Mumbai|Delhi|Hyderabad|Chennai|Pune',
            case=False,
            na=False
        ).astype(int)
        
        # 6. Stage filtering (keep seed to growth)
        valid_stages = ['Seed', 'Series A', 'Series B', 'Early Stage', 'Growth']
        self.df['has_valid_stage'] = self.df['Fund Stage'].notna()
        
        # Sort by quality: India-based > Active > Has stage info
        self.df = self.df.sort_values(
            by=['india_based', 'Number of Investments', 'has_valid_stage'],
            ascending=[False, False, False]
        )
        
        logger.info(f"\n📊 Final filtered dataset: {len(self.df)} investors")
        logger.info(f"   - India-based: {self.df['india_based'].sum()}")
        logger.info(f"   - With investments: {(self.df['Number of Investments'] > 0).sum()}")
        logger.info(f"   - With portfolio: {self.df['Portfolio Companies'].notna().sum()}")
    
    def parse_sectors(self, sectors_str):
        """Parse sector string into list"""
        if pd.isna(sectors_str):
            return ["Technology"]
        
        # Split by common delimiters
        sectors = re.split(r'[,;|/]', str(sectors_str))
        sectors = [s.strip() for s in sectors if s.strip()]
        
        # Limit to top 5 sectors
        return sectors[:5] if sectors else ["Technology"]
    
    def parse_portfolio(self, portfolio_str):
        """Parse portfolio companies string into list"""
        if pd.isna(portfolio_str):
            return []
        
        companies = re.split(r'[,;|]', str(portfolio_str))
        companies = [c.strip() for c in companies if c.strip()]
        
        # Limit to top 10 companies
        return companies[:10]
    
    def parse_stages(self, stage_str):
        """Parse investment stages"""
        if pd.isna(stage_str):
            return ["Seed", "Series A"]
        
        stages = re.split(r'[,;|]', str(stage_str))
        stages = [s.strip() for s in stages if s.strip()]
        
        return stages if stages else ["Seed", "Series A"]
    
    def estimate_ticket_size(self, fund_type, stage, investments_count):
        """
        Estimate ticket size based on fund type and stage
        Returns (min, max) in USD (millions)
        """
        
        # Angel investors
        if 'Angel' in str(fund_type):
            return (0.025, 0.5)  # $25K - $500K
        
        # Micro VC
        elif 'Micro' in str(fund_type):
            return (0.1, 1)  # $100K - $1M
        
        # Based on stage
        elif 'Seed' in str(stage):
            return (0.25, 2)  # $250K - $2M
        elif 'Series A' in str(stage) or 'Early' in str(stage):
            return (1, 5)  # $1M - $5M
        elif 'Series B' in str(stage) or 'Growth' in str(stage):
            return (5, 20)  # $5M - $20M
        
        # Active investors (many investments) likely have bigger tickets
        elif investments_count > 50:
            return (2, 10)  # $2M - $10M
        elif investments_count > 20:
            return (0.5, 5)  # $500K - $5M
        
        # Default
        else:
            return (0.25, 3)  # $250K - $3M
    
    def transform_to_weaviate_format(self, limit=None):
        """
        Transform DataFrame to Weaviate format
        
        Args:
            limit: Number of investors to process (None = all)
        """
        
        if limit:
            df_to_process = self.df.head(limit)
            logger.info(f"\n📦 Processing top {limit} investors...")
        else:
            df_to_process = self.df
            logger.info(f"\n📦 Processing all {len(df_to_process)} investors...")
        
        investors = []
        
        for idx, row in df_to_process.iterrows():
            
            # Parse sectors
            focus_areas = self.parse_sectors(row.get('Fund Focus (Sectors)'))
            
            # Parse portfolio
            portfolio = self.parse_portfolio(row.get('Portfolio Companies'))
            
            # Parse stages
            stages = self.parse_stages(row.get('Fund Stage'))
            
            # Estimate ticket size
            ticket_min, ticket_max = self.estimate_ticket_size(
                row.get('Fund Type'),
                row.get('Fund Stage'),
                row.get('Number of Investments', 0)
            )
            
            # Extract location (default to "India" if not specified)
            location = row.get('Location', 'India')
            if pd.isna(location) or str(location).strip() == '':
                location = 'India'
            else:
                location = str(location).strip()
            
            # Determine investor type
            fund_type = row.get('Fund Type', 'Venture Capital')
            if 'Angel' in str(fund_type):
                investor_type = 'Angel Investor'
            elif 'Micro' in str(fund_type):
                investor_type = 'Micro VC'
            else:
                investor_type = 'Venture Capital'
            
            # Build description
            description = row.get('Fund Description', '')
            if pd.isna(description) or str(description).strip() == '':
                description = f"{row.get('Investor Name')} is a {investor_type} focusing on {', '.join(focus_areas[:3])}."
            
            # Create searchable content
            content = f"{row.get('Investor Name')} | {investor_type} | {', '.join(focus_areas)} | {location} | {', '.join(stages)} | ${ticket_min}M-${ticket_max}M | {len(portfolio)} portfolio companies"
            if description:
                content += f" | {description[:200]}"
            
            investor = {
                "name": row.get('Investor Name', 'Unknown').strip(),
                "type": investor_type,
                "focus_areas": focus_areas,
                "location": location,
                "ticket_size_min": float(ticket_min),
                "ticket_size_max": float(ticket_max),
                "website": row.get('Website (if available)', ''),
                "contact_email": row.get('Partner Email', ''),
                "portfolio": portfolio,
                "investment_stages": stages,
                "number_of_investments": int(row.get('Number of Investments', 0)) if pd.notna(row.get('Number of Investments')) else 0,
                "number_of_exits": int(row.get('Number of Exits', 0)) if pd.notna(row.get('Number of Exits')) else 0,
                "description": description,
                "founding_year": int(row.get('Founding Year', 0)) if pd.notna(row.get('Founding Year')) else 0,
                "partner_name": row.get('Partner Name', ''),
                "twitter": row.get('Twitter Link', ''),
                "linkedin": row.get('LinkedIn Link', ''),
                "content": content,
                "_data_source": "Ramps VC Database",
                "_quality_score": row.get('quality_score', 0)
            }
            
            investors.append(investor)
        
        logger.info(f"✅ Transformed {len(investors)} investors")
        return investors
    
    async def load_to_weaviate(self, investors):
        """Load investors into Weaviate"""
        
        logger.info(f"\n🚀 Loading {len(investors)} investors to Weaviate...")
        
        try:
            # Batch load
            batch_size = 50
            for i in range(0, len(investors), batch_size):
                batch = investors[i:i+batch_size]
                await vector_store_service.add_documents("Investor", batch)
                logger.info(f"  Loaded batch {i//batch_size + 1}/{(len(investors)-1)//batch_size + 1}")
            
            logger.info("✅ All investors loaded successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error loading to Weaviate: {e}")
            raise
    
    def show_statistics(self):
        """Show statistics about the dataset"""
        
        logger.info("\n" + "="*60)
        logger.info("📊 DATASET STATISTICS")
        logger.info("="*60)
        
        logger.info(f"\nTotal investors: {len(self.df)}")
        
        # By type
        logger.info("\n🏢 By Type:")
        logger.info(self.df['Fund Type'].value_counts().head(10))
        
        # By location
        logger.info("\n📍 Top Locations:")
        logger.info(self.df['Location'].value_counts().head(10))
        
        # By stage
        logger.info("\n📈 By Stage:")
        logger.info(self.df['Fund Stage'].value_counts().head(10))
        
        # Investment activity
        logger.info("\n💼 Investment Activity:")
        logger.info(f"  Total investments tracked: {self.df['Number of Investments'].sum():.0f}")
        logger.info(f"  Avg investments per fund: {self.df['Number of Investments'].mean():.1f}")
        logger.info(f"  Most active: {self.df['Number of Investments'].max():.0f} investments")
        
        # Data quality
        logger.info("\n✅ Data Quality:")
        logger.info(f"  With website: {self.df['Website (if available)'].notna().sum()}")
        logger.info(f"  With email: {self.df['Partner Email'].notna().sum()}")
        logger.info(f"  With portfolio: {self.df['Portfolio Companies'].notna().sum()}")
        logger.info(f"  With description: {self.df['Fund Description'].notna().sum()}")

async def main():
    """Main ingestion pipeline"""
    
    # Path to your CSV file
    csv_path = str(
        Path(__file__).resolve().parents[2]
        / "Dataset"
        / "Ramp's Airtable database"
        / "Fund Database-Ramp's VC & Angel Email Database.csv"
    )
    
    logger.info("="*60)
    logger.info("🚀 INVESTOR DATA INGESTION PIPELINE")
    logger.info("="*60)
    
    # Initialize ingestion
    ingestion = InvestorDataIngestion(csv_path)
    
    # Step 1: Load CSV
    ingestion.load_csv()
    
    # Step 2: Show initial statistics
    logger.info("\n📊 INITIAL DATASET:")
    ingestion.show_statistics()
    
    # Step 3: Clean and filter
    ingestion.clean_and_filter()
    
    # Step 4: Show filtered statistics
    logger.info("\n📊 FILTERED DATASET:")
    ingestion.show_statistics()
    
    # Step 5: Ask how many to load
    logger.info("\n" + "="*60)
    logger.info("How many investors to load?")
    logger.info("="*60)
    logger.info("Options:")
    logger.info("  - 50:  Quick demo (recommended for hackathon)")
    logger.info("  - 100: Good coverage")
    logger.info("  - 200: Comprehensive")
    logger.info("  - 500: Very comprehensive")
    logger.info("  - all: Load everything (may take 5-10 min)")
    
    choice = input("\nEnter number (or 'all'): ").strip()
    
    if choice.lower() == 'all':
        limit = None
    else:
        try:
            limit = int(choice)
        except:
            logger.warning("Invalid input, using 50")
            limit = 50
    
    # Step 6: Transform data
    investors = ingestion.transform_to_weaviate_format(limit=limit)
    
    # Step 7: Show sample
    logger.info("\n📝 Sample investor data:")
    logger.info(f"Name: {investors[0]['name']}")
    logger.info(f"Type: {investors[0]['type']}")
    logger.info(f"Focus: {investors[0]['focus_areas']}")
    logger.info(f"Location: {investors[0]['location']}")
    logger.info(f"Ticket: ₹{investors[0]['ticket_size_min']}-{investors[0]['ticket_size_max']}Cr")
    logger.info(f"Portfolio: {len(investors[0]['portfolio'])} companies")
    
    # Step 8: Load to Weaviate
    confirm = input("\n✅ Proceed with loading to Weaviate? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        await ingestion.load_to_weaviate(investors)
        
        logger.info("\n" + "="*60)
        logger.info("🎉 INGESTION COMPLETE!")
        logger.info("="*60)
        logger.info(f"✅ Loaded {len(investors)} investors to Weaviate")
        logger.info("\nYou can now:")
        logger.info("  1. Start the server: python -m app.main")
        logger.info("  2. Test investor matching")
        logger.info("  3. Upload startup pitch decks")
    else:
        logger.info("Cancelled. No data was loaded.")

if __name__ == "__main__":
    asyncio.run(main())
