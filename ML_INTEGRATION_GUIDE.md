# Machine Learning Integration Guide

## 🎯 Tổng quan

Hệ thống đã tích hợp Machine Learning để:
1. **Dự đoán chất lượng code** (Random Forest)
2. **Phân loại issues** (Decision Trees)
3. **Phát hiện code tương tự** (K-NN + CodeBERT)
4. **Detect plagiarism** (Cosine Similarity)

---

## 📁 Files đã tạo

```
app/analysis/
├── ml_models.py           # ML model implementations
└── __init__.py

scripts/
└── train_ml_models.py     # Training scripts
```

---

## 🚀 Cách sử dụng

### 1. Training Models (Ban đầu hoặc định kỳ)

```bash
# Chạy training script
python scripts/train_ml_models.py

# Output: models được lưu vào thư mục models/
# - models/quality_predictor.joblib
# - models/issue_classifier.joblib
```

**Khi nào cần train:**
- Lần đầu setup hệ thống
- Cuối mỗi semester (có thêm data mới)
- Khi accuracy giảm
- Khi thêm features mới

### 2. Load Models vào Production

```python
# app/main.py
from app.analysis.ml_models import ml_models

@app.on_event("startup")
async def startup():
    # Load pre-trained models
    ml_models.load_models("models/")
    logger.info("ML models loaded")
```

### 3. Sử dụng trong Analysis Pipeline

```python
# app/controllers/analysis_controller.py
from app.analysis.ml_models import ml_models

async def analyze_code(session_id: str, code: str):
    # 1. Extract code metrics
    metrics = extract_code_metrics(code)
    
    # 2. Predict quality
    quality = await ml_models.predict_quality(metrics)
    # Result: {'quality': 'GOOD', 'confidence': 0.85, ...}
    
    # 3. Check plagiarism
    plagiarism = await ml_models.detect_plagiarism(code, threshold=0.85)
    if plagiarism:
        logger.warning("Plagiarism detected", data=plagiarism)
    
    # 4. Find similar code for hints
    similar = await ml_models.find_similar_code(code, k=3)
    
    return {
        'quality': quality,
        'plagiarism': plagiarism,
        'similar_submissions': similar
    }
```

---

## 📊 Model Performance Expectations

### Quality Predictor (Random Forest)
```
Expected Accuracy: 80-90%
Training time: ~2-5 minutes (1000 samples)
Prediction time: <10ms
Memory: ~50MB
```

### Issue Classifier (Random Forest)
```
Expected Accuracy: 70-85%
Training time: ~1-3 minutes
Prediction time: <5ms
Memory: ~30MB
```

### Similarity Detector (CodeBERT + K-NN)
```
Precision: 95%+
Search time: ~100ms (1000 samples)
Memory: ~200MB (with CodeBERT)
Index build time: ~5 minutes (1000 samples)
```

---

## 🎓 Training Data Requirements

### Minimum Dataset Sizes:
- **Quality Predictor**: 500-1000 labeled samples
- **Issue Classifier**: 200-500 labeled issues
- **Similarity Index**: 100+ code samples (càng nhiều càng tốt)

### Data Format:

**For Quality Predictor:**
```python
{
    'features': {
        'cyclomatic_complexity': 15,
        'lines_of_code': 250,
        'num_methods': 12,
        'num_classes': 3,
        'max_nesting_depth': 4,
        'comment_ratio': 0.15,
        'duplicate_ratio': 0.05
    },
    'label': 'GOOD'  # EXCELLENT | GOOD | FAIR | POOR
}
```

**For Similarity Index:**
```python
{
    'code': "class MainActivity : AppCompatActivity() { ... }",
    'metadata': {
        'student_id': 'student_123',
        'assignment_id': 'hw1',
        'timestamp': '2024-01-15'
    }
}
```

---

## 🔧 Cold Start Problem Solutions

### Vấn đề: Không có data ban đầu

**Solution 1: Synthetic Data**
```python
# Generate synthetic training data
def generate_synthetic_data(n_samples=500):
    """
    Tạo data giả dựa trên:
    - Good code examples từ instructor
    - Common mistakes patterns
    - Random variations
    """
    data = []
    for _ in range(n_samples):
        features = {
            'cyclomatic_complexity': np.random.randint(5, 50),
            'lines_of_code': np.random.randint(50, 500),
            # ... other features
        }
        label = assign_label_based_on_rules(features)
        data.append({'features': features, 'label': label})
    
    return data
```

**Solution 2: Pre-trained Models**
```python
# Sử dụng CodeBERT pre-trained
from transformers import AutoModel

# Model đã được train trên millions of code samples
model = AutoModel.from_pretrained("microsoft/codebert-base")
```

**Solution 3: Import External Data**
```python
# Import từ GitHub, Kaggle
# - Java/Kotlin code quality datasets
# - Bug detection datasets
# - Code smell datasets
```

**Solution 4: Rule-based Fallback**
```python
class HybridAnalyzer:
    """
    Nếu ML model chưa có/chưa train:
    → Fallback về rule-based analysis
    """
    async def analyze(self, code):
        if self.ml_model.is_trained:
            return await self.ml_model.predict(code)
        else:
            return self.rule_based_analyzer.analyze(code)
```

---

## 📈 Model Monitoring & Retraining

### 1. Track Model Performance

```python
class ModelMonitor:
    """Monitor model accuracy over time"""
    
    async def log_prediction(self, prediction, actual_label=None):
        await prisma.mlprediction.create(data={
            'prediction': prediction,
            'actual_label': actual_label,
            'timestamp': datetime.utcnow()
        })
    
    async def check_accuracy(self, window_days=30):
        """Check accuracy over last N days"""
        predictions = await prisma.mlprediction.find_many(
            where={
                'timestamp': {'gte': datetime.utcnow() - timedelta(days=window_days)},
                'actual_label': {'not': None}
            }
        )
        
        correct = sum(1 for p in predictions if p.prediction == p.actual_label)
        accuracy = correct / len(predictions) if predictions else 0
        
        if accuracy < 0.75:  # Threshold
            logger.warning("Model accuracy dropped", accuracy=accuracy)
            # Trigger retraining
        
        return accuracy
```

### 2. Automatic Retraining

```python
# Schedule via Celery
from celery import Celery

@celery.task
def retrain_models_task():
    """
    Scheduled task to retrain models
    Run: Weekly, Monthly, or when accuracy drops
    """
    asyncio.run(train_quality_predictor())
    asyncio.run(train_issue_classifier())
```

---

## 🎯 Feature Engineering Tips

### Good Features for Code Quality:

**Structural Features:**
- Cyclomatic Complexity (McCabe)
- Lines of Code (LOC)
- Number of classes/methods
- Max nesting depth
- Inheritance depth

**Quality Metrics:**
- Comment ratio
- Test coverage
- Code duplication ratio
- Naming convention adherence

**Android-specific:**
- Uses recommended components (RecyclerView, ViewModel, etc.)
- Follows architecture patterns (MVVM, MVP)
- Resource management (proper lifecycle handling)

### Feature Extraction Example:

```python
import radon.complexity as radon_cc
import radon.metrics as radon_metrics

def extract_features(code: str) -> dict:
    """Extract features from code using radon"""
    
    # Cyclomatic complexity
    cc = radon_cc.cc_visit(code)
    avg_complexity = np.mean([block.complexity for block in cc])
    
    # Raw metrics
    metrics = radon_metrics.mi_visit(code, multi=True)
    
    # LOC
    loc = code.count('\n')
    
    # Comment ratio
    comment_lines = sum(1 for line in code.split('\n') if line.strip().startswith('//'))
    comment_ratio = comment_lines / loc if loc > 0 else 0
    
    return {
        'cyclomatic_complexity': avg_complexity,
        'lines_of_code': loc,
        'comment_ratio': comment_ratio,
        # ... more features
    }
```

---

## 💾 Model Storage & Versioning

```
models/
├── v1/
│   ├── quality_predictor.joblib
│   ├── issue_classifier.joblib
│   └── metadata.json
├── v2/
│   ├── quality_predictor.joblib
│   ├── issue_classifier.joblib
│   └── metadata.json
└── current -> v2/  # Symlink to current version
```

**Metadata format:**
```json
{
    "version": "v2",
    "trained_at": "2024-01-15T10:30:00Z",
    "training_samples": 1500,
    "accuracy": 0.87,
    "features": [
        "cyclomatic_complexity",
        "lines_of_code",
        "..."
    ],
    "hyperparameters": {
        "n_estimators": 100,
        "max_depth": 15
    }
}
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Model overfitting
**Symptom:** High training accuracy, low test accuracy

**Solution:**
```python
# Reduce model complexity
rf = RandomForestClassifier(
    n_estimators=50,      # Reduce from 100
    max_depth=10,         # Limit depth
    min_samples_split=20  # Increase minimum split
)

# Use cross-validation
from sklearn.model_selection import cross_val_score
scores = cross_val_score(rf, X, y, cv=5)
```

### Issue 2: Imbalanced classes
**Symptom:** Model biased to majority class

**Solution:**
```python
# Option 1: Class weights
rf = RandomForestClassifier(class_weight='balanced')

# Option 2: SMOTE oversampling
from imblearn.over_sampling import SMOTE
smote = SMOTE()
X_balanced, y_balanced = smote.fit_resample(X, y)
```

### Issue 3: Slow predictions
**Symptom:** ML predictions take >1 second

**Solution:**
```python
# Option 1: Reduce model size
rf = RandomForestClassifier(n_estimators=20)  # Instead of 100

# Option 2: Use simpler model
from sklearn.tree import DecisionTreeClassifier
dt = DecisionTreeClassifier(max_depth=10)

# Option 3: Cache predictions
from functools import lru_cache

@lru_cache(maxsize=1000)
def predict_cached(code_hash):
    return model.predict(code_features)
```

---

## 🎯 Roadmap

### Phase 1 (Now): Basic ML ✅
- [x] Random Forest quality predictor
- [x] Decision Tree issue classifier  
- [x] K-NN similarity detector
- [x] Training scripts

### Phase 2 (Next 2-3 months):
- [ ] Collect real training data
- [ ] Fine-tune models
- [ ] Add XGBoost models
- [ ] Implement feature importance analysis
- [ ] A/B testing framework

### Phase 3 (3-6 months):
- [ ] Deep Learning models (CodeBERT fine-tuning)
- [ ] Ensemble models
- [ ] Online learning (incremental updates)
- [ ] AutoML for hyperparameter tuning

---

## 📚 Resources

**Libraries Used:**
- scikit-learn: Classical ML models
- sentence-transformers: Code embeddings
- joblib: Model serialization
- radon: Python code metrics
- tree-sitter: AST parsing

**Pre-trained Models:**
- microsoft/codebert-base
- microsoft/graphcodebert-base
- Salesforce/codet5-base

**Datasets (for transfer learning):**
- CodeSearchNet
- BigQuery GitHub dataset
- Code smell datasets on Kaggle

---

## 🎓 Kết luận

ML đã được tích hợp sẵn nhưng cần:
1. ✅ Có thể chạy ngay với rule-based fallback
2. 📊 Cần thu thập data để train models
3. 🔄 Setup periodic retraining
4. 📈 Monitor performance over time

**Current Status:** MVP ready, can start collecting data! 🚀
