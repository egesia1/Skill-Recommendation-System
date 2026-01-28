#!/usr/bin/env python3
"""
Example: Train ESCO Recommendation Model

Usage:
    python examples/train_esco.py --db_path data/esco.db --output_dir models --language en
"""

import sys
import os
import argparse
import logging

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.trainer import train_esco_model

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Train ESCO recommendation model using WALS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Train with default parameters
    python examples/train_esco.py --db_path data/esco.db --output_dir models
    
    # Train with custom parameters
    python examples/train_esco.py --db_path data/esco.db --output_dir models \\
        --language en --factors 100 --regularization 0.05 --iterations 20
        """
    )
    
    parser.add_argument('--db_path', type=str, required=True,
                       help='Path to ESCO SQLite database file')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Output directory for saved model')
    parser.add_argument('--language', type=str, default='en',
                       help='ESCO language code (default: en)')
    parser.add_argument('--factors', type=int, default=50,
                       help='Number of latent factors (default: 50)')
    parser.add_argument('--regularization', type=float, default=0.1,
                       help='Regularization parameter (default: 0.1)')
    parser.add_argument('--iterations', type=int, default=15,
                       help='Number of WALS iterations (default: 15)')
    parser.add_argument('--w_0', type=float, default=0.01,
                       help='Weight for unobserved entries (default: 0.01)')
    parser.add_argument('--save_history', action='store_true',
                       help='Save training history for each iteration')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.db_path):
        logger.error(f"Database file not found: {args.db_path}")
        sys.exit(1)
    
    try:
        result = train_esco_model(
            db_path=args.db_path,
            output_dir=args.output_dir,
            language=args.language,
            factors=args.factors,
            regularization=args.regularization,
            iterations=args.iterations,
            w_0=args.w_0,
            save_history=args.save_history
        )
        
        logger.info("Training completed successfully!")
        logger.info(f"Model file: {result['model_path']}")
        logger.info(f"Training time: {result['total_time']:.2f} seconds")
        
        if result.get('initial_error') and result.get('final_error'):
            error_reduction = result['initial_error'] - result['final_error']
            reduction_pct = (error_reduction / result['initial_error']) * 100
            logger.info(f"Error reduction: {error_reduction:.2f} ({reduction_pct:.2f}%)")
        
    except Exception as e:
        logger.error(f"Error during training: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
