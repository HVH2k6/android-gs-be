"""
Script import training samples vào API
Usage: python import_samples.py
"""
import requests
import json
import sys

API_BASE = "http://localhost:8000/api/ml-training"

def create_dataset():
    """Create a new dataset"""
    print("📦 Creating dataset...")
    response = requests.post(f"{API_BASE}/datasets", json={
        "name": "Android Quality Training Dataset v1",
        "description": "Dataset chứa code samples để train quality predictor với 4 levels: EXCELLENT, GOOD, FAIR, POOR"
    })

    if response.status_code == 200:
        dataset = response.json()
        print(f"✅ Dataset created: {dataset['id']}")
        return dataset['id']
    else:
        print(f"❌ Error creating dataset: {response.status_code}")
        print(response.text)
        sys.exit(1)

def add_samples(dataset_id, samples):
    """Add code samples to dataset"""
    print(f"\n📝 Adding {len(samples)} samples...")

    success_count = 0
    for i, sample in enumerate(samples, 1):
        response = requests.post(
            f"{API_BASE}/datasets/{dataset_id}/samples",
            json=sample
        )

        if response.status_code == 200:
            success_count += 1
            if i % 5 == 0:
                print(f"  Added {i}/{len(samples)} samples...")
        else:
            print(f"❌ Error adding sample {i}: {response.status_code}")

    print(f"✅ Successfully added {success_count}/{len(samples)} samples")
    return success_count

def get_dataset_info(dataset_id):
    """Get dataset information"""
    response = requests.get(f"{API_BASE}/datasets")
    if response.status_code == 200:
        datasets = response.json()
        dataset = next((d for d in datasets if d['id'] == dataset_id), None)
        if dataset:
            print(f"\n📊 Dataset Info:")
            print(f"  Name: {dataset['name']}")
            print(f"  Total samples: {dataset['total_samples']}")
            print(f"  Quality distribution: {dataset['quality_distribution']}")
        return dataset
    return None

def main():
    # Load samples from generated file
    try:
        with open("training_samples.json", "r", encoding="utf-8") as f:
            samples = json.load(f)
    except FileNotFoundError:
        print("❌ training_samples.json not found!")
        print("Run: python generate_training_samples.py first")
        sys.exit(1)

    print("🚀 Starting import process...\n")

    # Create dataset
    dataset_id = create_dataset()

    # Add samples
    success_count = add_samples(dataset_id, samples)

    # Show final info
    get_dataset_info(dataset_id)

    print(f"\n✅ Import complete!")
    print(f"Dataset ID: {dataset_id}")
    print(f"Ready for training!")

if __name__ == "__main__":
    main()
