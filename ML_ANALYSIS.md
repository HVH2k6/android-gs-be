# Phân tích áp dụng Machine Learning cho hệ thống phân tích code học tập

## 🎯 Bối cảnh
Hệ thống Android Learning Monitoring cần phân tích code của sinh viên và đưa ra feedback. ML có thể hỗ trợ:
- Phát hiện code patterns (tốt/xấu)
- Dự đoán lỗi tiềm ẩn
- Gợi ý cải thiện
- Đánh giá chất lượng code
- Phát hiện plagiarism
- Dự đoán thời gian hoàn thành

---

## 📊 Các thuật toán ML phù hợp

### 1️⃣ **K-Nearest Neighbors (K-NN)** ⭐ Có thể áp dụng

#### ✅ **Use Cases phù hợp:**

**A. Code Similarity Detection (Phát hiện code tương tự)**
```python
from sklearn.neighbors import NearestNeighbors
from sentence_transformers import SentenceTransformer

class CodeSimilarityDetector:
    def __init__(self):
        self.model = SentenceTransformer('microsoft/codebert-base')
        self.knn = NearestNeighbors(n_neighbors=5, metric='cosine')
        
    def find_similar_code(self, student_code, k=5):
        """
        Tìm k đoạn code tương tự nhất từ database
        Dùng để:
        - Phát hiện plagiarism
        - Gợi ý code mẫu
        - So sánh với bài làm của sinh viên khác
        """
        # Embed code thành vector
        code_embedding = self.model.encode([student_code])
        
        # Tìm k láng giềng gần nhất
        distances, indices = self.knn.kneighbors(code_embedding)
        
        return {
            'similar_submissions': indices[0],
            'similarity_scores': 1 - distances[0]  # Cosine similarity
        }
```

**B. Code Quality Prediction**
```python
class CodeQualityPredictor:
    """
    Dự đoán chất lượng code dựa trên:
    - Code metrics (LOC, complexity, coupling)
    - AST features
    - Historical data
    """
    def predict_quality(self, code_features):
        # Features: [complexity, loc, num_classes, avg_method_length, ...]
        # Label: [EXCELLENT, GOOD, FAIR, POOR]
        
        neighbors = self.knn.kneighbors([code_features])
        # Majority vote từ k láng giềng
        return self.majority_vote(neighbors)
```

#### ⚖️ **Lợi & Hại của K-NN**

**✅ Ưu điểm:**
1. **Simple & Intuitive**: Dễ hiểu, dễ implement
2. **No Training Phase**: Không cần train model, chỉ cần lưu data
3. **Non-parametric**: Không giả định về phân phối data
4. **Incremental Learning**: Thêm data mới không cần retrain
5. **Good for Small Datasets**: Hoạt động tốt với dataset nhỏ ban đầu

**❌ Nhược điểm:**
1. **Slow Prediction**: O(n) cho mỗi query - chậm khi có nhiều sinh viên
2. **Memory Intensive**: Phải lưu toàn bộ training data
3. **Curse of Dimensionality**: Kém hiệu quả với nhiều features
4. **Sensitive to Noise**: Dữ liệu nhiễu ảnh hưởng lớn
5. **Need Feature Engineering**: Phải chọn features tốt

**💡 Giải pháp tối ưu:**
```python
# Sử dụng Approximate Nearest Neighbors cho tốc độ
from annoy import AnnoyIndex

class FastCodeSimilarity:
    def __init__(self, embedding_dim=768):
        self.index = AnnoyIndex(embedding_dim, 'angular')  # Cosine
        
    def build_index(self, code_embeddings):
        """Build index 1 lần, query nhanh"""
        for i, embedding in enumerate(code_embeddings):
            self.index.add_item(i, embedding)
        self.index.build(10)  # 10 trees
        
    def find_similar(self, query_embedding, k=5):
        """Query O(log n) thay vì O(n)"""
        return self.index.get_nns_by_vector(query_embedding, k)
```

---

### 2️⃣ **Decision Trees / Random Forest** ⭐⭐ Rất phù hợp

#### ✅ **Use Cases tuyệt vời:**

**A. Code Issue Classification**
```python
from sklearn.ensemble import RandomForestClassifier

class CodeIssueClassifier:
    """
    Phân loại vấn đề code:
    - BUG (null pointer, resource leak, ...)
    - CODE_SMELL (long method, god class, ...)
    - PERFORMANCE (inefficient algorithm, ...)
    - SECURITY (SQL injection, XSS, ...)
    """
    def __init__(self):
        self.rf = RandomForestClassifier(n_estimators=100)
        
    def train(self, X_features, y_labels):
        """
        Features có thể bao gồm:
        - AST node types count
        - Cyclomatic complexity
        - Number of parameters
        - Method length
        - Depth of inheritance
        - Coupling between objects
        """
        self.rf.fit(X_features, y_labels)
        
    def predict_with_explanation(self, code_features):
        """Decision Tree có thể explain được quyết định"""
        prediction = self.rf.predict([code_features])[0]
        
        # Feature importance
        importances = self.rf.feature_importances_
        
        return {
            'issue_type': prediction,
            'confidence': self.rf.predict_proba([code_features]).max(),
            'key_factors': self.get_top_features(importances)
        }
```

**B. Assignment Requirement Checker**
```python
class RequirementChecker:
    """
    Kiểm tra code có đáp ứng requirements không
    Ví dụ: "Phải có ít nhất 3 classes", "Phải sử dụng RecyclerView"
    """
    def check_requirements(self, code_ast, requirements):
        features = self.extract_features(code_ast)
        
        # Decision Tree cho từng requirement
        results = {}
        for req in requirements:
            tree = self.requirement_trees[req.id]
            results[req.id] = {
                'passed': tree.predict([features])[0],
                'reason': self.explain_decision(tree, features)
            }
        return results
```

#### ⚖️ **Lợi & Hại của Decision Trees**

**✅ Ưu điểm:**
1. **Interpretable**: Dễ hiểu, có thể visualize decision path
2. **No Feature Scaling**: Không cần normalize features
3. **Handles Mixed Data**: Numeric + Categorical cùng lúc
4. **Feature Importance**: Biết feature nào quan trọng
5. **Fast Prediction**: O(log n) với balanced tree
6. **Can Capture Non-linear Relationships**

**❌ Nhược điểm:**
1. **Overfitting**: Single tree dễ overfit (→ dùng Random Forest)
2. **Unstable**: Thay đổi nhỏ trong data → tree khác hoàn toàn
3. **Biased to Dominant Classes**: Cần balance dataset
4. **Not Good for Extrapolation**: Chỉ predict trong range đã thấy

**💡 Best Practices:**
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

class RobustCodeAnalyzer:
    def __init__(self):
        # Random Forest để giảm overfitting
        self.rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,          # Giới hạn depth
            min_samples_split=10,  # Tránh split quá nhiều
            class_weight='balanced' # Balance classes
        )
        
    def train_with_validation(self, X, y):
        # Cross-validation để đánh giá
        scores = cross_val_score(self.rf, X, y, cv=5)
        print(f"CV Score: {scores.mean():.3f} (+/- {scores.std():.3f})")
        
        self.rf.fit(X, y)
```

---

### 3️⃣ **Các thuật toán ML khác nên xem xét**

#### **A. Gradient Boosting (XGBoost, LightGBM)** ⭐⭐⭐ Highly Recommended

**Tại sao tốt hơn Decision Tree:**
- Accuracy cao hơn
- Ít overfitting hơn
- Fast training & prediction
- Built-in feature importance

```python
from xgboost import XGBClassifier

class AdvancedCodeAnalyzer:
    def __init__(self):
        self.xgb = XGBClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
```

**Use cases:**
- Code quality scoring (0-100)
- Bug prediction
- Estimate time to complete
- Predict student performance

#### **B. Neural Networks (Deep Learning)** ⭐⭐⭐

**Code Embeddings với Transformers:**
```python
from transformers import AutoModel, AutoTokenizer

class CodeBERTAnalyzer:
    """
    Sử dụng pre-trained models:
    - microsoft/codebert-base
    - microsoft/graphcodebert-base
    - Salesforce/codet5-base
    """
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        self.model = AutoModel.from_pretrained("microsoft/codebert-base")
        
    def get_code_embedding(self, code):
        """Vector representation của code"""
        inputs = self.tokenizer(code, return_tensors="pt", truncation=True)
        outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1)  # 768-dim vector
```

**Use cases:**
- Code similarity (plagiarism detection)
- Code search
- Bug detection
- Code completion suggestions

#### **C. Clustering (K-Means, DBSCAN)** ⭐⭐

**Nhóm sinh viên theo code patterns:**
```python
from sklearn.cluster import KMeans

class StudentClustering:
    """
    Nhóm sinh viên để:
    - Phát hiện nhóm cần help nhiều hơn
    - Tạo peer learning groups
    - Detect common mistakes
    """
    def cluster_students(self, student_features):
        kmeans = KMeans(n_clusters=5)
        clusters = kmeans.fit_predict(student_features)
        
        return {
            'cluster_labels': clusters,
            'cluster_centers': kmeans.cluster_centers_,
            'insights': self.analyze_clusters(clusters)
        }
```

---

## 🏗️ **Kiến trúc ML Pipeline đề xuất**

```python
class MLAnalysisPipeline:
    """
    Multi-stage ML pipeline cho code analysis
    """
    
    def __init__(self):
        # Stage 1: Feature Extraction
        self.feature_extractor = CodeFeatureExtractor()
        
        # Stage 2: Traditional ML
        self.quality_predictor = XGBClassifier()      # XGBoost
        self.issue_classifier = RandomForestClassifier()  # Decision Tree
        
        # Stage 3: Deep Learning
        self.code_embedder = CodeBERTModel()          # Embeddings
        self.similarity_finder = AnnoyIndex()          # K-NN
        
        # Stage 4: Rule-based (fallback)
        self.rule_engine = StaticAnalysisRules()
        
    async def analyze_code(self, student_code, assignment):
        # Step 1: Extract features
        features = self.feature_extractor.extract(student_code)
        
        # Step 2: Predict quality
        quality = self.quality_predictor.predict(features)
        
        # Step 3: Classify issues
        issues = self.issue_classifier.predict(features)
        
        # Step 4: Find similar code
        embedding = self.code_embedder.encode(student_code)
        similar_codes = self.similarity_finder.query(embedding)
        
        # Step 5: Rule-based checks (always run)
        rule_violations = self.rule_engine.check(student_code)
        
        # Step 6: Combine results
        return self.combine_results(
            quality, issues, similar_codes, rule_violations
        )
```

---

## 📊 **So sánh các approach**

| Approach | Accuracy | Speed | Interpretability | Maintenance | Data Required |
|----------|----------|-------|------------------|-------------|---------------|
| Rule-based | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | None |
| Decision Tree | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Medium |
| Random Forest | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Medium |
| XGBoost | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Medium |
| K-NN | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medium |
| Deep Learning | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | Large |
| LLM (GPT/Claude) | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | None |

---

## 🎯 **Đề xuất Implementation Strategy**

### **Phase 1: MVP (1-2 tháng)** - Rule-based + Simple ML
```python
# ✅ Làm ngay
- Static analysis (AST parsing, lint rules)
- Basic metrics (LOC, complexity)
- Decision Tree cho requirement checking
- K-NN cho code similarity (với Annoy)
```

### **Phase 2: Enhanced (2-3 tháng)** - Advanced ML
```python
# ✅ Sau khi có data
- Random Forest / XGBoost cho bug prediction
- Code quality scoring
- Clustering students
- Feature importance analysis
```

### **Phase 3: Advanced (3-6 tháng)** - Deep Learning
```python
# ✅ Khi có nhiều data và resources
- CodeBERT embeddings
- Fine-tune pre-trained models
- Custom neural networks
- Ensemble models
```

### **Phase 4: Production (ongoing)** - Hybrid Approach
```python
# ✅ Best of all worlds
class HybridAnalyzer:
    """
    Kết hợp:
    - Rule-based (fast, accurate cho known patterns)
    - ML models (patterns phức tạp)
    - LLM (explanation, creative feedback)
    """
```

---

## 💾 **Data Requirements**

### **Training Data cần thu thập:**
1. **Labeled Code Samples:**
   - Good code examples (từ instructor)
   - Bad code examples (common mistakes)
   - Bug examples với labels
   
2. **Historical Student Data:**
   - Past submissions
   - Grades / feedback
   - Time to complete
   - Revision history

3. **Code Features:**
   ```python
   features = {
       'structural': {
           'num_classes': 5,
           'num_methods': 20,
           'max_nesting_depth': 4,
           'cyclomatic_complexity': 15,
           'lines_of_code': 250,
       },
       'quality': {
           'comment_ratio': 0.15,
           'test_coverage': 0.75,
           'code_duplication': 0.05,
       },
       'android_specific': {
           'uses_recyclerview': True,
           'uses_viewmodel': True,
           'follows_mvvm': False,
       }
   }
   ```

### **Minimum Dataset Size:**
- Decision Tree / Random Forest: **500-1000 samples**
- K-NN: **100-500 samples** (nhưng càng nhiều càng tốt)
- Deep Learning: **10,000+ samples**
- Transfer Learning (CodeBERT): **500-1000 samples** (fine-tuning)

---

## ⚠️ **Challenges & Mitigation**

### **Challenge 1: Cold Start Problem**
❌ Không có data ban đầu

✅ **Solutions:**
1. Sử dụng synthetic data (generate từ templates)
2. Pre-trained models (CodeBERT, CodeT5)
3. Rule-based system trong giai đoạn đầu
4. Import data từ GitHub / Kaggle

### **Challenge 2: Imbalanced Classes**
❌ Nhiều "good code", ít "bad code"

✅ **Solutions:**
```python
from imblearn.over_sampling import SMOTE

# Oversample minority class
smote = SMOTE()
X_balanced, y_balanced = smote.fit_resample(X_train, y_train)

# Hoặc dùng class weights
rf = RandomForestClassifier(class_weight='balanced')
```

### **Challenge 3: Feature Engineering**
❌ Khó extract features từ code

✅ **Solutions:**
1. Sử dụng AST (tree-sitter)
2. Code metrics libraries (radon, pylint)
3. Pre-trained embeddings (CodeBERT)

### **Challenge 4: Model Maintenance**
❌ Model degradation over time

✅ **Solutions:**
```python
class ModelMonitoring:
    """
    Track model performance
    Retrain khi accuracy drop
    """
    def monitor_predictions(self):
        if self.accuracy < threshold:
            self.trigger_retraining()
```

---

## 📈 **Expected Performance**

### **Với hybrid approach (Rule + ML + LLM):**

```
├─ Code Quality Detection: ~85-90% accuracy
├─ Bug Detection: ~70-80% accuracy
├─ Requirement Checking: ~90-95% accuracy
├─ Code Similarity: ~95%+ precision
├─ Response Time: <2 seconds (without LLM)
└─ Scalability: 1000+ students đồng thời
```

---

## 🎯 **KẾT LUẬN**

### ✅ **NÊN áp dụng ML:**

1. **Decision Tree / Random Forest** ⭐⭐⭐⭐⭐
   - Requirement checking
   - Issue classification
   - Quality prediction
   
2. **K-NN (với Annoy optimization)** ⭐⭐⭐⭐
   - Code similarity
   - Plagiarism detection
   
3. **XGBoost** ⭐⭐⭐⭐⭐
   - Overall quality scoring
   - Bug prediction
   
4. **CodeBERT (Transfer Learning)** ⭐⭐⭐⭐
   - Code embeddings
   - Semantic analysis

### ⚖️ **KHÔNG nên:**
- ❌ Pure Deep Learning từ scratch (cần quá nhiều data)
- ❌ Bỏ rule-based hoàn toàn (vẫn cần cho known patterns)
- ❌ K-NN thuần (chậm, dùng Annoy hoặc FAISS)

### 🎯 **Recommended Stack:**

```python
ML_STACK = {
    "feature_extraction": "tree-sitter + radon",
    "classical_ml": "scikit-learn + xgboost",
    "deep_learning": "transformers (CodeBERT)",
    "similarity": "sentence-transformers + annoy",
    "monitoring": "mlflow",
    "deployment": "FastAPI + Celery"
}
```

### 📊 **ROI Estimate:**
- Development time: 2-3 tháng
- Accuracy improvement: +30-40% vs pure rule-based
- Maintenance: Medium (retrain mỗi semester)
- **Worth it!** 🚀
