"""
Ingest Startup Company Data from CSV
Intelligently filters and structures data for Weaviate - for Investor Discovery
"""

import pandas as pd
import asyncio
import logging
from app.services.vector_store_service import vector_store_service
from app.services.embedding_service import embedding_service
import re
from datetime import datetime


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StartupDataIngestion:
    """Ingest startup company data for investor matching"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
    
    def load_csv(self):
        """Load and inspect CSV"""
        logger.info(f"Loading CSV from {self.csv_path}")
        
        # Verify file exists
        import os
        if not os.path.exists(self.csv_path):
            logger.error(f"❌ CSV file not found: {self.csv_path}")
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        logger.info(f"✅ CSV file exists, size: {os.path.getsize(self.csv_path)} bytes")
        
        self.df = pd.read_csv(self.csv_path, encoding='utf-8')

        # Normalize column names (strip whitespace)
        self.df.columns = [c.strip() for c in self.df.columns]
        required_cols = [
            'Company Name', 'Website', 'Industry', 'Funding Status', 'One Liner',
            'Description', 'Year Founded', 'Last Funding', 'Total Funding', 'Investors',
            'Twitter', 'LinkedIn', 'Facebook', 'Contact Email', 'HQ Location'
        ]
        missing = [c for c in required_cols if c not in self.df.columns]
        if missing:
            logger.warning(f"⚠️ Missing expected columns: {missing}")
            logger.info(f"Available columns: {self.df.columns.tolist()}")
        
        logger.info(f"✅ Loaded {len(self.df)} rows from CSV")
        logger.info(f"📋 Columns: {self.df.columns.tolist()}")
        
        # Show sample
        logger.info("\n📝 Sample data (first 2 rows):")
        for idx, row in self.df.head(2).iterrows():
            logger.info(f"  Row {idx}: {row.get('Company Name', 'N/A')}")
    
    def clean_and_filter(self):
        """
        Clean data and apply smart filters
        Keep only high-quality, relevant startups
        """
        
        logger.info("\n" + "="*60)
        logger.info("Filtering for quality startups...")
        logger.info("="*60)
        
        original_count = len(self.df)
        logger.info(f"Starting with {original_count} rows")
        
        # 1. Remove rows with missing critical fields (Company Name)
        before = len(self.df)
        self.df = self.df.dropna(subset=['Company Name'])
        removed = before - len(self.df)
        logger.info(f"✓ Removed {removed} entries with no company name → {len(self.df)} remaining")
        
        # 2. Remove empty company names
        before = len(self.df)
        self.df = self.df[self.df['Company Name'].str.strip() != '']
        removed = before - len(self.df)
        logger.info(f"✓ Removed {removed} blank company names → {len(self.df)} remaining")
        
        # 3. Calculate quality score based on data completeness
        self.df['quality_score'] = (
            self.df['Website'].notna().astype(int) +
            self.df['Industry'].notna().astype(int) +
            self.df['Description'].notna().astype(int) +
            self.df['Total Funding'].notna().astype(int) +
            self.df['Investors'].notna().astype(int) +
            self.df['Year Founded'].notna().astype(int) +
            (self.df['Contact Email'].notna() | self.df['LinkedIn'].notna()).astype(int)
        )
        
        # Keep startups with quality_score >= 2
        before_quality = len(self.df)
        self.df = self.df[self.df['quality_score'] >= 2]
        removed = before_quality - len(self.df)
        logger.info(f"✓ Kept high-quality entries (score >= 2): {len(self.df)} remaining (removed {removed})")
        
        # 4. Prioritize by funding (higher funded = more established)
        self.df['funding_numeric'] = self.df['Total Funding'].apply(self._parse_funding_amount)
        self.df = self.df.sort_values('funding_numeric', ascending=False, na_position='last')
        
        # 5. Geographic tagging (prioritize India-based but keep international)
        self.df['india_based'] = self.df['HQ Location'].str.contains(
            'India|Bangalore|Bengaluru|Mumbai|Delhi|Hyderabad|Chennai|Pune|Gurgaon|Noida|Kolkata',
            case=False,
            na=False
        ).astype(int)
        
        # 6. Stage tagging based on funding status
        self.df['stage'] = self.df['Funding Status'].apply(self._determine_stage)
        
        # Sort by: India-based > Funding amount > Quality score
        self.df = self.df.sort_values(
            by=['india_based', 'funding_numeric', 'quality_score'],
            ascending=[False, False, False]
        )
        
        logger.info(f"\n✅ Final filtered dataset: {len(self.df)} startups")
        logger.info(f"   - India-based: {self.df['india_based'].sum()}")
        logger.info(f"   - With funding data: {self.df['Total Funding'].notna().sum()}")
        logger.info(f"   - With investors: {self.df['Investors'].notna().sum()}")
    
    def _parse_funding_amount(self, funding_str):
        """Parse funding string to numeric value (in USD)"""
        if pd.isna(funding_str):
            return 0
        
        funding_str = str(funding_str).upper().replace(',', '').replace('$', '').strip()
        
        try:
            # Handle M (millions) and B (billions)
            if 'B' in funding_str:
                num = float(re.sub(r'[^\d.]', '', funding_str))
                return num * 1000000000
            elif 'M' in funding_str:
                num = float(re.sub(r'[^\d.]', '', funding_str))
                return num * 1000000
            elif 'K' in funding_str:
                num = float(re.sub(r'[^\d.]', '', funding_str))
                return num * 1000
            else:
                return float(re.sub(r'[^\d.]', '', funding_str)) if funding_str else 0
        except:
            return 0
    
    def _determine_stage(self, funding_status):
        """Determine startup stage from funding status"""
        if pd.isna(funding_status):
            return "Unknown"
        
        status = str(funding_status).lower()
        
        if 'seed' in status:
            return "Seed"
        elif 'series a' in status:
            return "Series A"
        elif 'series b' in status:
            return "Series B"
        elif 'series c' in status:
            return "Series C"
        elif 'series d' in status or 'series e' in status or 'series f' in status:
            return "Late Stage"
        elif 'ipo' in status or 'public' in status:
            return "Public"
        elif 'acquired' in status:
            return "Acquired"
        elif 'pre-seed' in status or 'pre seed' in status:
            return "Pre-Seed"
        elif 'angel' in status:
            return "Angel"
        else:
            return "Unknown"
    
    def _parse_investors(self, investors_str):
        """Parse investors string into list"""
        if pd.isna(investors_str):
            return []
        
        # Split by common delimiters
        investors = re.split(r'[,;|]', str(investors_str))
        investors = [i.strip() for i in investors if i.strip()]
        
        # Limit to top 15 investors
        return investors[:15]
    
    def _parse_industry(self, industry_str):
        """Parse industry/sector string"""
        if pd.isna(industry_str):
            return "Technology"
        
        industry = str(industry_str).strip()
        
        # Normalize common industries
        industry_lower = industry.lower()
        
        if 'fintech' in industry_lower or 'financial' in industry_lower:
            return "Fintech"
        elif 'health' in industry_lower or 'medical' in industry_lower or 'biotech' in industry_lower:
            return "Healthcare"
        elif 'edtech' in industry_lower or 'education' in industry_lower:
            return "Edtech"
        elif 'ecommerce' in industry_lower or 'e-commerce' in industry_lower or 'retail' in industry_lower:
            return "E-commerce"
        elif 'saas' in industry_lower or 'software' in industry_lower:
            return "SaaS"
        elif 'ai' in industry_lower or 'machine learning' in industry_lower or 'artificial' in industry_lower:
            return "AI/ML"
        elif 'food' in industry_lower or 'agri' in industry_lower:
            return "AgriTech/FoodTech"
        elif 'logistics' in industry_lower or 'supply chain' in industry_lower:
            return "Logistics"
        elif 'real estate' in industry_lower or 'proptech' in industry_lower:
            return "PropTech"
        elif 'gaming' in industry_lower or 'entertainment' in industry_lower:
            return "Gaming/Entertainment"
        elif 'clean' in industry_lower or 'energy' in industry_lower or 'climate' in industry_lower:
            return "CleanTech"
        elif 'cyber' in industry_lower or 'security' in industry_lower:
            return "Cybersecurity"
        else:
            return industry[:50] if industry else "Technology"
    
    def _format_funding_display(self, amount):
        """Format funding amount for display"""
        if amount >= 1000000000:
            return f"${amount/1000000000:.1f}B"
        elif amount >= 1000000:
            return f"${amount/1000000:.1f}M"
        elif amount >= 1000:
            return f"${amount/1000:.0f}K"
        elif amount > 0:
            return f"${amount:.0f}"
        else:
            return "Undisclosed"
    
    def transform_to_weaviate_format(self, limit=None):
        """
        Transform DataFrame to Weaviate format
        
        Args:
            limit: Number of startups to process (None = all)
        """
        
        if limit:
            df_to_process = self.df.head(limit)
            logger.info(f"\n📦 Processing top {limit} startups...")
        else:
            df_to_process = self.df
            logger.info(f"\n📦 Processing all {len(df_to_process)} startups...")
        
        startups = []
        skipped = 0
        
        for idx, row in df_to_process.iterrows():
            
            # Parse and clean data
            company_name = str(row.get('Company Name', 'Unknown')).strip()
            if not company_name or company_name == 'nan':
                logger.debug(f"  Skipping row {idx}: no company name")
                skipped += 1
                continue
            
            # Parse industry/sector
            sector = self._parse_industry(row.get('Industry'))
            
            # Parse investors
            investors = self._parse_investors(row.get('Investors'))
            
            # Parse funding amount
            funding_amount_usd = self._parse_funding_amount(row.get('Total Funding'))
            funding_display = self._format_funding_display(funding_amount_usd)
            
            # Get stage
            stage = row.get('stage', 'Unknown')
            if stage == 'Unknown':
                stage = self._determine_stage(row.get('Funding Status'))
            
            # Location
            location = row.get('HQ Location', '')
            if pd.isna(location) or str(location).strip() == '':
                location = 'Not specified'
            else:
                location = str(location).strip()
            
            # Description
            description = row.get('Description', '')
            if pd.isna(description):
                description = row.get('One Liner', '')
            if pd.isna(description) or str(description).strip() == '':
                description = f"{company_name} is a {sector} startup."
            else:
                description = str(description).strip()[:500]
            
            # One liner / Problem statement
            one_liner = row.get('One Liner', '')
            if pd.isna(one_liner):
                one_liner = description[:100] if description else ''
            else:
                one_liner = str(one_liner).strip()
            
            # Website
            website = row.get('Website', '')
            if pd.isna(website):
                website = ''
            else:
                website = str(website).strip()
            
            # Contact email
            contact_email = row.get('Contact Email', '')
            if pd.isna(contact_email):
                contact_email = ''
            else:
                contact_email = str(contact_email).strip()
            
            # Year founded
            year_founded = row.get('Year Founded', 0)
            try:
                year_founded = int(year_founded) if pd.notna(year_founded) else 0
            except:
                year_founded = 0
            
            # Last funding date
            last_funding = row.get('Last Funding', '')
            if pd.isna(last_funding):
                last_funding = ''
            else:
                last_funding = str(last_funding).strip()

            # Created date: prefer last funding date if parseable, else now
            # RFC3339 format: YYYY-MM-DDTHH:MM:SSZ
            created_date = None
            try:
                if last_funding:
                    # Try common date formats
                    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%b %d, %Y", "%Y"):
                        try:
                            dt = datetime.strptime(last_funding, fmt)
                            # Format as RFC3339: strip microseconds and add Z for UTC
                            created_date = dt.replace(microsecond=0).isoformat() + "Z"
                            break
                        except Exception:
                            continue
            except Exception:
                created_date = None
            if not created_date:
                # Current UTC time in RFC3339 format
                created_date = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            
            # Social links
            twitter = str(row.get('Twitter', '')) if pd.notna(row.get('Twitter')) else ''
            linkedin = str(row.get('LinkedIn', '')) if pd.notna(row.get('LinkedIn')) else ''
            facebook = str(row.get('Facebook', '')) if pd.notna(row.get('Facebook')) else ''
            
            # Create searchable content for vector embedding
            content = f"{company_name} | {sector} | {stage} | {location} | {funding_display}"
            if investors:
                content += f" | Investors: {', '.join(investors[:5])}"
            content += f" | {description[:300]}"
            
            startup = {
                "startup_name": company_name,
                "founder_name": "",  # Not in CSV
                "sector": sector,
                "stage": stage,
                "location": location,
                # Store numeric amount in USD for uniformity
                "funding_amount": float(funding_amount_usd) if funding_amount_usd else 0.0,
                "description": description,
                "problem_statement": one_liner,
                "solution": "",  # Not in CSV
                "market_size": "",  # Not in CSV
                "business_model": "",  # Not in CSV
                "traction": "",  # Not in CSV
                "team_size": 0,  # Not in CSV
                "revenue": 0,  # Not in CSV
                "content": content,
                "pitch_deck_url": "",  # Not in CSV
                "contact_email": contact_email,
                "website": website,
                "created_date": created_date,
                # Additional fields for richer data
                "_investors": investors,
                "_investors_str": ', '.join(investors) if investors else '',
                "_total_funding": row.get('Total Funding', ''),
                "_last_funding_date": last_funding,
                "_year_founded": year_founded,
                "_twitter": twitter,
                "_linkedin": linkedin,
                "_facebook": facebook,
                "_funding_status": str(row.get('Funding Status', '')) if pd.notna(row.get('Funding Status')) else '',
                "_data_source": "Startup Database CSV",
                "_quality_score": row.get('quality_score', 0),
                "_india_based": row.get('india_based', 0)
            }
            
            startups.append(startup)
        
        logger.info(f"✅ Transformed {len(startups)} startups (skipped {skipped})")
        if not startups:
            logger.error("❌ No startups were transformed! Check CSV data quality.")
        return startups
    
    async def load_to_weaviate(self, startups):
        """Reset Startup collection and load startups into Weaviate"""
        
        if not startups:
            logger.error("❌ No startups to load! Aborting.")
            return False
        
        logger.info(f"\n🧹 Resetting Startup collection before load")
        try:
            ok = vector_store_service.recreate_collection("Startup")
            if ok:
                logger.info("✅ Startup collection recreated successfully")
            else:
                logger.warning("⚠️ Could not recreate Startup collection; proceeding with existing")
        except Exception as e:
            logger.warning(f"⚠️ Startup collection reset failed: {e}")
        
        logger.info(f"\n🚀 Loading {len(startups)} startups to Weaviate...")
        
        try:
            # Batch load
            batch_size = 50
            total_batches = (len(startups) - 1) // batch_size + 1
            
            for i in range(0, len(startups), batch_size):
                batch = startups[i:i+batch_size]
                batch_num = i // batch_size + 1
                logger.info(f"  Loading batch {batch_num}/{total_batches} ({len(batch)} items)...")
                
                try:
                    success = await vector_store_service.add_documents("Startup", batch, generate_embeddings=True)
                    if success:
                        logger.info(f"  ✅ Batch {batch_num} loaded successfully")
                    else:
                        logger.error(f"  ❌ Batch {batch_num} failed to load")
                except Exception as e:
                    logger.error(f"  ❌ Error loading batch {batch_num}: {e}")
                    raise
            
            logger.info("\n✅ All startups loaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading to Weaviate: {e}")
            raise
    
    def show_statistics(self):
        """Show statistics about the dataset"""
        
        logger.info("\n" + "="*60)
        logger.info("📊 DATASET STATISTICS")
        logger.info("="*60)
        
        logger.info(f"\nTotal startups: {len(self.df)}")
        
        # By industry
        logger.info("\n🏢 Top Industries:")
        logger.info(self.df['Industry'].value_counts().head(15))
        
        # By funding status
        logger.info("\n💰 By Funding Status:")
        logger.info(self.df['Funding Status'].value_counts().head(10))
        
        # By location
        logger.info("\n📍 Top Locations:")
        logger.info(self.df['HQ Location'].value_counts().head(10))
        
        # By stage (derived)
        if 'stage' in self.df.columns:
            logger.info("\n📈 By Stage (Derived):")
            logger.info(self.df['stage'].value_counts())
        
        # Funding statistics
        if 'funding_numeric' in self.df.columns:
            funded = self.df[self.df['funding_numeric'] > 0]
            logger.info("\n💵 Funding Statistics:")
            logger.info(f"  Startups with funding data: {len(funded)}")
            if len(funded) > 0:
                logger.info(f"  Total funding tracked: ${funded['funding_numeric'].sum()/1e9:.2f}B")
                logger.info(f"  Average funding: ${funded['funding_numeric'].mean()/1e6:.2f}M")
                logger.info(f"  Median funding: ${funded['funding_numeric'].median()/1e6:.2f}M")
                logger.info(f"  Max funding: ${funded['funding_numeric'].max()/1e9:.2f}B")
        
        # Data quality
        logger.info("\n✅ Data Quality:")
        logger.info(f"  With website: {self.df['Website'].notna().sum()}")
        logger.info(f"  With description: {self.df['Description'].notna().sum()}")
        logger.info(f"  With investors: {self.df['Investors'].notna().sum()}")
        logger.info(f"  With contact email: {self.df['Contact Email'].notna().sum()}")
        logger.info(f"  With LinkedIn: {self.df['LinkedIn'].notna().sum()}")


async def main():
    """Main ingestion pipeline"""
    
    import os
    
    # Try multiple possible CSV paths
    possible_paths = [
        # Absolute path
        "D:\\AI-Verse Hackathon\\Dataset\\Ramp's Airtable database\\Company Database-Grid view.csv",
        # Relative path from backend
        "../../Dataset/Ramp's Airtable database/Company Database-Grid view.csv",
        # Relative path with spaces
        "../../Dataset/Rampa Airtable database/Company Database-Grid view.csv",
    ]
    
    csv_path = None
    for path in possible_paths:
        expanded = os.path.expanduser(path)
        if os.path.exists(expanded):
            csv_path = expanded
            logger.info(f"✅ Found CSV at: {csv_path}")
            break
    
    if not csv_path:
        logger.error("❌ CSV file not found. Tried:")
        for path in possible_paths:
            logger.error(f"   - {path}")
        logger.error("\n⚠️ Please update the CSV path in the script and try again.")
        return
    
    logger.info("="*60)
    logger.info("🚀 STARTUP DATA INGESTION PIPELINE")
    logger.info("="*60)
    
    # Initialize ingestion
    ingestion = StartupDataIngestion(csv_path)
    
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
    logger.info("How many startups to load?")
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
    startups = ingestion.transform_to_weaviate_format(limit=limit)
    
    # Check if we have data to load
    if not startups:
        logger.error("\\n❌ NO STARTUPS WERE TRANSFORMED!")
        logger.error("Possible causes:")
        logger.error("  1. CSV data quality is too low (all rows filtered out)")
        logger.error("  2. Company Name column is missing or empty")
        logger.error("  3. Quality score filtering is too strict")
        logger.error("\\nDebug info:")
        if hasattr(ingestion, 'df'):
            logger.error(f"  - Total rows before filtering: {len(ingestion.df)}")
            has_col = 'Company Name' in ingestion.df.columns
            logger.error(f"  - Company Name column exists: {has_col}")
        return
    
    # Step 7: Show sample
    if startups:
        logger.info("\n📝 Sample startup data:")
        sample = startups[0]
        logger.info(f"Name: {sample['startup_name']}")
        logger.info(f"Sector: {sample['sector']}")
        logger.info(f"Stage: {sample['stage']}")
        logger.info(f"Location: {sample['location']}")
        logger.info(f"Funding: {sample.get('_total_funding', 'N/A')}")
        logger.info(f"Investors: {sample.get('_investors_str', 'N/A')[:100]}...")
        logger.info(f"Description: {sample['description'][:100]}...")
    
    # Step 8: Load to Weaviate
    confirm = input("\n✅ Proceed with loading to Weaviate? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        await ingestion.load_to_weaviate(startups)
        
        logger.info("\n" + "="*60)
        logger.info("🎉 INGESTION COMPLETE!")
        logger.info("="*60)
        logger.info(f"✅ Loaded {len(startups)} startups to Weaviate")
        logger.info("\nYou can now:")
        logger.info("  1. Start the server: python -m app.main")
        logger.info("  2. Browse startups as an investor")
        logger.info("  3. Match startups with investors")
    else:
        logger.info("Cancelled. No data was loaded.")


if __name__ == "__main__":
    asyncio.run(main())
