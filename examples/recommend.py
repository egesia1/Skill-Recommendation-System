#!/usr/bin/env python3
"""
Example: Generate Skill Recommendations

Usage:
    python examples/recommend.py --model_path models/esco_wmf_model_en.pkl \\
        --skill_uris "skill_uri_1" "skill_uri_2" "skill_uri_3" --top_k 20
"""

import sys
import os
import argparse
import logging

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.recommender import load_model, recommend_skills

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Generate skill recommendations from trained model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # ESCO recommendations
    python examples/recommend.py --model_path models/esco_wmf_model_en.pkl \\
        --skill_uris "http://data.europa.eu/esco/skill/..." \\
        --top_k 20
    
    # ONET task model (input = task IDs from Task Statements)
    python examples/recommend.py --model_path models/onet_task_wmf_model.pkl \\
        --skill_uris "8823" "8824" "8825" --top_k 20

    # ONET technology skill model (input = software/tool names, e.g. Example)
    python examples/recommend.py --model_path models/onet_tech_skill_wmf_model.pkl \\
        --skill_uris "Adobe Acrobat" "Microsoft Excel" --top_k 20
        """
    )
    
    parser.add_argument('--model_path', type=str, required=True,
                       help='Path to trained model .pkl file')
    parser.add_argument('--skill_uris', type=str, nargs='+', required=True,
                       help='Input skill URIs (or element_ids for ONET)')
    parser.add_argument('--top_k', type=int, default=20,
                       help='Number of recommendations (default: 20)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.model_path):
        logger.error(f"Model file not found: {args.model_path}")
        sys.exit(1)
    
    try:
        # Load model
        logger.info(f"Loading model from: {args.model_path}")
        model_data = load_model(args.model_path)
        
        # Generate recommendations
        logger.info(f"Generating recommendations for {len(args.skill_uris)} input skills...")
        recommendations = recommend_skills(
            model_data=model_data,
            input_skill_uris=args.skill_uris,
            top_k=args.top_k,
            filter_existing=True
        )
        
        # Display results
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        print(f"\nInput Skills ({len(args.skill_uris)}):")
        for i, skill_uri in enumerate(args.skill_uris, 1):
            print(f"  {i}. {skill_uri}")
        
        print(f"\nTop {len(recommendations)} Recommended Skills:")
        print("-" * 80)
        for i, (skill_uri, score) in enumerate(recommendations, 1):
            print(f"{i:3d}. Score: {score:8.4f} | {skill_uri}")
        
        print("\n" + "="*80)
        logger.info("Recommendations generated successfully!")
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
