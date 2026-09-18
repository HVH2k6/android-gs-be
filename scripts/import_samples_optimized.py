"""
OPTIMIZED Script import training samples vào API
Features:
- Batch processing
- Progress tracking
- Error recovery
- Validation
Usage: python import_samples.py [--batch-size 10]
"""
import requests
import json
import sys
import time
from typing import List, Dict

API_BASE = "http://localhost:8000/api/ml-training"
BATCH_SIZE = 10  # Process in batches for better performance

def print_progress_bar(iteration, total, prefix='', suffix='', length=50):
    """Print progress bar"""
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='')
    if iteration == total:
        print()

def create_dataset():
    """Create a new dataset"""
    print("📦 Creating dataset...")
    response = requests.post(f"{API_BASE}/datasets", json={
        "name": "Android Quality Training Dataset v1 (Optimized)",
        "description": "100+ samples covering EXCELLENT, GOOD, FAIR, POOR quality levels with diverse patterns"
    })

    if response.status_code == 200:
        dataset = response.json()
        print(f"✅ Dataset created: {dataset['id']}")
        return dataset['id']
    else:
        print(f"❌ Error creating dataset: {response.status_code}")
        print(response.text)
        sys.exit(1)

def add_samples_batch(dataset_id: str, samples: List[Dict], batch_size: int = BATCH_SIZE):
    """Add code samples in batches with progress tracking"""
    total = len(samples)
    print(f"\n📝 Adding {total} samples in batches of {batch_size}...")

    success_count = 0
    failed_samples = []

    for i in range(0, total, batch_size):
        batch = samples[i:i + batch_size]

        for j, sample in enumerate(batch):
            try:
                response = requests.post(
                    f"{API_BASE}/datasets/{dataset_id}/samples",
                    json=sample,
                    timeout=10
                )

                if response.status_code == 200:
                    success_count += 1
                else:
                    failed_samples.append((i + j, sample['file_path'], response.status_code))
            except Exception as e:
                failed_samples.append((i + j, sample['file_path'], str(e)))

            # Update progress
            print_progress_bar(
                i + j + 1,
                total,
                prefix='Progress:',
                suffix=f'Complete ({success_count}/{total} successful)'
            )

        # Small delay between batches to avoid overwhelming server
        if i + batch_size < total:
            time.sleep(0.1)

    print(f"\n✅ Successfully added {success_count}/{total} samples")

    if failed_samples:
        print(f"\n⚠️  {len(failed_samples)} samples failed:")
        for idx, file_path, error in failed_samples[:5]:  # Show first 5
            print(f"  [{idx}] {file_path}: {error}")
        if len(failed_samples) > 5:
            print(f"  ... and {len(failed_samples) - 5} more")

    return success_count, failed_samples

def validate_samples(samples: List[Dict]) -> tuple:
    """Validate samples before import"""
    print("\n🔍 Validating samples...")

    valid = []
    invalid = []

    for i, sample in enumerate(samples):
        if not sample.get('code') or not sample.get('code').strip():
            invalid.append((i, "Empty code"))
        elif sample.get('quality_label') not in ['EXCELLENT', 'GOOD', 'FAIR', 'POOR']:
            invalid.append((i, f"Invalid quality label: {sample.get('quality_label')}"))
        elif not sample.get('file_path'):
            invalid.append((i, "Missing file_path"))
        else:
            valid.append(sample)

    if invalid:
        print(f"⚠️  Found {len(invalid)} invalid samples:")
        for idx, reason in invalid[:3]:
            print(f"  [{idx}] {reason}")

    print(f"✅ {len(valid)} valid samples ready for import")
    return valid, invalid

def get_dataset_info(dataset_id: str):
    """Get and display dataset information"""
    response = requests.get(f"{API_BASE}/datasets")
    if response.status_code == 200:
        datasets = response.json()
        dataset = next((d for d in datasets if d['id'] == dataset_id), None)
        if dataset:
            print(f"\n📊 Dataset Summary:")
            print(f"  Name: {dataset['name']}")
            print(f"  Total samples: {dataset['total_samples']}")
            print(f"  Distribution:")
            for quality, count in sorted(dataset['quality_distribution'].items()):
                percentage = (count / dataset['total_samples'] * 100) if dataset['total_samples'] > 0 else 0
                print(f"    {quality:12s}: {count:3d} ({percentage:5.1f}%)")
        return dataset
    return None

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import training samples')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Batch size for processing')
    parser.add_argument('--file', type=str, default='training_samples.json', help='Input JSON file')
    args = parser.parse_args()

    print("🚀 OPTIMIZED Training Data Import\n")

    # Load samples
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            samples = json.load(f)
        print(f"📁 Loaded {len(samples)} samples from {args.file}")
    except FileNotFoundError:
        print(f"❌ File not found: {args.file}")
        print("💡 Run: python generate_training_samples.py first")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)

    # Validate samples
    valid_samples, invalid_samples = validate_samples(samples)

    if not valid_samples:
        print("❌ No valid samples to import!")
        sys.exit(1)

    # Create dataset
    dataset_id = create_dataset()

    # Import samples
    start_time = time.time()
    success_count, failed = add_samples_batch(dataset_id, valid_samples, args.batch_size)
    elapsed = time.time() - start_time

    # Show results
    get_dataset_info(dataset_id)

    print(f"\n⏱️  Time elapsed: {elapsed:.2f}s")
    print(f"⚡ Speed: {success_count / elapsed:.1f} samples/sec")
    print(f"\n✅ Import complete!")
    print(f"📦 Dataset ID: {dataset_id}")
    print(f"🎯 Ready for training!")

    if failed:
        print(f"\n⚠️  Note: {len(failed)} samples failed to import")
        print("    Check error messages above for details")

if __name__ == "__main__":
    main()
