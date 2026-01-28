#!/usr/bin/env python3
"""
Example: Train ONET recommendation models (task and/or technology skill).

Usage:
    python examples/train_onet.py --db_path data/onet.db --output_dir models
    python examples/train_onet.py --db_path data/onet.db --output_dir models --type task
    python examples/train_onet.py --db_path data/onet.db --output_dir models --type tech_skill
"""

import sys
import os
import argparse
import logging

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.trainer import train_onet_task_model, train_onet_technology_skill_model

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Train ONET recommendation models (task and/or technology skill) using WALS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Train both task and tech_skill models (default)
    python examples/train_onet.py --db_path data/onet.db --output_dir models

    # Train only task model -> models/onet_task_wmf_model.pkl
    python examples/train_onet.py --db_path data/onet.db --output_dir models --type task

    # Train only technology skill model -> models/onet_tech_skill_wmf_model.pkl
    python examples/train_onet.py --db_path data/onet.db --output_dir models --type tech_skill

    # Custom parameters
    python examples/train_onet.py --db_path data/onet.db --output_dir models \\
        --type task --factors 100 --regularization 0.05 --iterations 20
        """
    )

    parser.add_argument('--db_path', type=str, required=True,
                        help='Path to ONET SQLite database file')
    parser.add_argument('--output_dir', type=str, required=True,
                        help='Output directory for saved models')
    parser.add_argument('--type', type=str, choices=['task', 'tech_skill'],
                        help='Train only task or tech_skill model; if omitted, train both')
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

    types_to_train = ['task', 'tech_skill'] if args.type is None else [args.type]
    results = []

    try:
        if 'task' in types_to_train:
            result = train_onet_task_model(
                db_path=args.db_path,
                output_dir=args.output_dir,
                factors=args.factors,
                regularization=args.regularization,
                iterations=args.iterations,
                w_0=args.w_0,
                save_history=args.save_history
            )
            results.append(result)
            logger.info(f"Task model: {result['model_path']} ({result['total_time']:.2f}s)")
            if result.get('initial_error') and result.get('final_error'):
                err_red = result['initial_error'] - result['final_error']
                logger.info(f"  Error reduction: {err_red:.2f} ({(err_red / result['initial_error']) * 100:.2f}%)")

        if 'tech_skill' in types_to_train:
            result = train_onet_technology_skill_model(
                db_path=args.db_path,
                output_dir=args.output_dir,
                factors=args.factors,
                regularization=args.regularization,
                iterations=args.iterations,
                w_0=args.w_0,
                save_history=args.save_history
            )
            results.append(result)
            logger.info(f"Tech skill model: {result['model_path']} ({result['total_time']:.2f}s)")
            if result.get('initial_error') and result.get('final_error'):
                err_red = result['initial_error'] - result['final_error']
                logger.info(f"  Error reduction: {err_red:.2f} ({(err_red / result['initial_error']) * 100:.2f}%)")

        logger.info("Training completed successfully!")
    except Exception as e:
        logger.error(f"Error during training: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
