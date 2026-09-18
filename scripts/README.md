# Training Data Generation Guide

Hướng dẫn tạo và import training data cho ML model.

## 📊 Khuyến nghị số lượng mẫu

### Minimum (để test): **10-20 samples**
- Đủ để start training
- Accuracy thấp (~60-70%)

### Recommended (production): **50-100 samples**
- EXCELLENT: 15-25 samples
- GOOD: 15-25 samples  
- FAIR: 15-25 samples
- POOR: 15-25 samples

### Optimal: **200-500 samples**
- Mỗi quality level: 50-125 samples
- Accuracy cao (~85-95%)
- Cover nhiều edge cases

## 🚀 Cách sử dụng

### Bước 1: Generate sample data

```bash
cd back-end/scripts
python generate_training_samples.py
```

Tạo file `training_samples.json` với ~8 samples mẫu (2 per quality level).

### Bước 2: Chỉnh sửa và thêm samples (Recommended)

Mở `training_samples.json` và thêm code samples thật từ projects:

```json
[
  {
    "code": "class MainActivity : AppCompatActivity() { ... }",
    "language": "kotlin",
    "quality_label": "GOOD",
    "file_path": "MainActivity.kt"
  }
]
```

**Tips:**
- Copy code từ projects Android thật
- Label dựa trên best practices
- EXCELLENT: Clean, MVVM, no leaks
- GOOD: Functional, minor issues
- FAIR: Works but có code smells
- POOR: Memory leaks, bad practices

### Bước 3: Start backend

```bash
cd back-end
python -m uvicorn main:app --reload
```

### Bước 4: Import vào database

```bash
cd back-end/scripts
python import_samples.py
```

Output:
```
🚀 Starting import process...

📦 Creating dataset...
✅ Dataset created: abc123...

📝 Adding 8 samples...
  Added 5/8 samples...
✅ Successfully added 8/8 samples

📊 Dataset Info:
  Name: Android Quality Training Dataset v1
  Total samples: 8
  Quality distribution: {'EXCELLENT': 2, 'GOOD': 2, 'FAIR': 2, 'POOR': 2}

✅ Import complete!
```

### Bước 5: Train model trong dashboard

1. Mở http://localhost:3000/models
2. Chuyển sang tab "Training Jobs"
3. Click "Start Training"
4. Chọn dataset vừa tạo
5. Chọn model type: `quality_predictor`
6. Click "Start Training"

## 📈 Quality Labels Guide

### EXCELLENT
- Follows MVVM/Clean Architecture
- Uses ViewModel + LiveData/Flow
- No memory leaks
- Proper error handling
- Good naming conventions
- Comments where needed

### GOOD
- Functional and readable
- Some architecture patterns
- Minor improvements needed
- Could be more modular

### FAIR
- Works but has issues
- Mixed responsibilities
- Some code smells
- High complexity
- Needs refactoring

### POOR
- Memory leaks (Context in companion)
- No architecture
- findViewById everywhere
- Nested callbacks
- Very high complexity
- Hard to maintain

## 🎯 Training Tips

1. **Balanced dataset**: Mỗi quality level nên có số lượng tương đương
2. **Diverse samples**: Đa dạng về complexity, LOC, patterns
3. **Real code**: Dùng code thật thay vì synthetic
4. **Consistent labeling**: Áp dụng tiêu chí labeling nhất quán

## 🔧 Troubleshooting

### Error: "Dataset must have at least 10 samples"
- Thêm samples vào `training_samples.json`
- Hoặc giảm minimum trong controller

### Import failed với 404
- Đảm bảo backend đang chạy
- Check API URL: `http://localhost:8000/api/ml-training`

### Training failed
- Check backend logs
- Đảm bảo code samples valid (parse được)

## 📁 File Structure

```
back-end/
├── scripts/
│   ├── generate_training_samples.py  # Generate mẫu
│   ├── import_samples.py             # Import vào API
│   └── training_samples.json         # Data samples (generated)
└── app/
    └── controllers/
        └── ml_training_controller.py # Training logic
```

## 🚀 Next Steps

1. **Collect more data**: Thu thập code từ projects thật
2. **Validate labels**: Review và ensure labeling chính xác
3. **Train multiple times**: So sánh accuracy
4. **Test predictions**: Test với code mới để verify
5. **Iterate**: Thêm samples cho cases model predict sai

---

**Note:** Với 50-100 samples cân bằng, model thường đạt ~80-85% accuracy. Để đạt >90%, cần 200-500 samples với labeling chính xác.
