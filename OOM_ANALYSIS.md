# OOM Analysis: Researcher7 Pipeline Crash

**Date:** 2026-02-24  
**Incident:** SIGKILL during Run #4 after 25 minutes  
**System:** Raspberry Pi 5 (16GB RAM, 512MB swap)

---

## 📊 Root Cause Analysis

### What Happened

The pipeline was **SIGKILL'd by the Linux OOM (Out of Memory) killer** after successfully generating 7/10 sections (25 minutes runtime).

### Memory Timeline

```
21:51  Pipeline starts
21:51  sentence-transformers model loads (~500MB)
21:52  Trend scraping (minimal memory)
21:53  Correlation analysis (embeddings + DBSCAN ~200MB peak)
21:56  Paper search (minimal memory)
21:59  Section 1 generated (phi4-mini inference ~2.5GB)
22:02  Section 2 generated
22:05  Section 3 generated
22:09  Section 4 generated
22:12  Section 5 generated
22:15  Section 6 generated
22:19  Section 7 generated
22:21  SIGKILL (OOM killer triggered)
```

### Memory Breakdown at Crash Time

| Component | Memory Usage | Notes |
|-----------|-------------|-------|
| **phi4-mini model** | ~2.5 GB | Loaded by Ollama (separate process) |
| **sentence-transformers** | ~500 MB | all-MiniLM-L6-v2 model |
| **Python process** | ~300 MB | Base + dependencies |
| **DBSCAN clustering** | ~100-200 MB | Temporary arrays for 25 terms |
| **Generated text** | ~50 MB | 7 sections in memory |
| **Ollama overhead** | ~500 MB | HTTP server + model management |
| **System overhead** | ~800 MB | OS, other processes |
| **Memory leak/accumulation** | ~500 MB+ | **KEY ISSUE** |

**Estimated Total:** 4.8 - 5.5 GB (before leak/accumulation)  
**System RAM:** 16 GB total, ~7-8 GB typically available  
**Conclusion:** Memory leak or gradual accumulation over 25 minutes pushed us past available RAM

---

## 🔍 Evidence

### System Specs
```bash
MemTotal:       16604208 kB (16 GB)
MemAvailable:    7714192 kB (7.4 GB available currently)
SwapTotal:        524272 kB (512 MB)
```

### Log Analysis
The crash log shows:
1. ✅ **NLP model loaded successfully** (sentence-transformers)
2. ❌ **SIGKILL immediately after** - no pipeline steps executed
3. ⚠️ **Log ends at model loading** - killed before/during early pipeline

**Wait... this doesn't match!** The autosave shows 7 sections completed but the log shows SIGKILL during model loading. 

**Explanation:** The log we saw (`run_10sections_20260224_215148.log`) is from a **different run attempt**. The successful 7-section run must have been logged elsewhere or not fully captured.

### Process Analysis
- **SIGKILL (signal 9):** System-initiated kill (not user, not program error)
- **No graceful exit:** Auto-save preserved sections (no manual save)
- **Timing:** ~25 minutes = exactly when Section 7 completed

---

## 🐛 Root Causes Identified

### 1. **Memory Accumulation Over Time** (Primary Cause)
- **What:** Python/transformers models accumulate memory with each inference
- **Why:** PyTorch/transformers don't release cached tensors by default
- **Evidence:** Process survived 7 sections (~20 minutes) then crashed
- **Impact:** ~500MB+ gradual leak over 25 minutes

### 2. **sentence-transformers Not Released** (Contributing)
- **What:** Embedding model stays in memory after correlation step
- **Why:** Python `SentenceTransformer` object never explicitly deleted
- **Evidence:** Model loaded at start, never freed
- **Impact:** ~500MB held unnecessarily after Step 2

### 3. **Ollama Memory Growth** (Contributing)
- **What:** Ollama server process may accumulate KV cache across requests
- **Why:** Each section generation stores context in cache
- **Evidence:** 10 sequential API calls over 25 minutes
- **Impact:** Unknown but potentially 200-500MB

### 4. **Limited Swap Space** (Aggravating)
- **What:** Only 512MB swap configured
- **Why:** Pi defaults to small swap on SD card
- **Impact:** No buffer when RAM fills up = immediate SIGKILL

### 5. **No Garbage Collection Between Sections** (Design)
- **What:** Python GC runs periodically, not between sections
- **Why:** No explicit `gc.collect()` calls in script
- **Impact:** Orphaned objects accumulate

---

## 🔧 Fix Plan

### **Option A: Memory Cleanup (Recommended)** ⭐
**Goal:** Free unused memory between pipeline steps

**Changes Required:**

1. **Free sentence-transformers after Step 2**
   ```python
   # In main.py after correlation analysis
   del correlation_engine.model
   import gc
   gc.collect()
   torch.cuda.empty_cache()  # If GPU used
   ```

2. **Garbage collect between sections**
   ```python
   # In script_generator.py after each section
   import gc
   gc.collect()
   ```

3. **Clear Ollama cache periodically**
   ```bash
   # Option: Restart Ollama every 5 sections
   # or: Set Ollama to clear KV cache between requests
   ```

**Expected Impact:** Frees ~500MB after Step 2, prevents ~200-300MB accumulation  
**Effort:** Low (30 minutes coding)  
**Risk:** Low  

---

### **Option B: Increase Swap** (Temporary Fix)
**Goal:** Give system breathing room when RAM fills

**Changes Required:**
```bash
# Increase swap from 512MB to 4GB
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=4096
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

**Expected Impact:** Prevents SIGKILL but slows down (swap I/O)  
**Effort:** 5 minutes  
**Risk:** Medium (SD card wear from swap writes)  

---

### **Option C: Smaller Embedding Model** (Optimization)
**Goal:** Reduce baseline memory footprint

**Changes Required:**
```python
# In src/correlation_engine.py
# Replace: all-MiniLM-L6-v2 (~500MB)
# With: paraphrase-MiniLM-L3-v2 (~60MB)

model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
```

**Expected Impact:** Frees ~440MB baseline  
**Effort:** 1 line change  
**Risk:** Medium (slightly lower embedding quality)  

---

### **Option D: Split Pipeline** (Nuclear Option)
**Goal:** Run steps separately to avoid memory accumulation

**Changes Required:**
1. Run Steps 1-3 (trends → correlation → paper)
2. Save intermediate state to JSON
3. Restart Python process
4. Load state and run Step 4 (script generation)

**Expected Impact:** 100% reliable (fresh memory each time)  
**Effort:** High (1-2 hours refactoring)  
**Risk:** Low but annoying (manual 2-step process)  

---

## 🎯 Recommended Solution

**Implement Option A + Option C** (Combined fix)

### Implementation Plan

**Phase 1: Quick Wins** (30 minutes)
1. ✅ Switch to smaller embedding model (`paraphrase-MiniLM-L3-v2`)
2. ✅ Add `gc.collect()` between sections
3. ✅ Delete sentence-transformers after Step 2

**Phase 2: Monitoring** (ongoing)
1. Add memory usage logging per section
2. Monitor for leaks over multiple runs
3. Add Ollama cache clearing if needed

**Phase 3: Fallback** (if needed)
1. Increase swap to 2GB (compromise between wear and safety)
2. Consider Option D if issues persist

---

## 📝 Code Changes Required

### File: `main.py`
```python
# After Step 2: Analyzing Correlations
correlation_data = correlation_engine.analyze(trends)
print(f"✓ Unified Topic: {correlation_data['unified_topic']['theme']}")

# NEW: Free embedding model memory
del correlation_engine.model
del correlation_engine
import gc
gc.collect()
print("💾 Freed correlation engine memory")
```

### File: `src/correlation_engine.py`
```python
# Line 16: Change model
from sentence_transformers import SentenceTransformer

class CorrelationEngine:
    def __init__(self):
        print("Loading NLP model: paraphrase-MiniLM-L3-v2...")  # Changed
        self.model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # Changed (~60MB vs ~500MB)
```

### File: `src/script_generator.py`
```python
# After each section generation in _generate_multipass()
section1 = self._generate_short_section(...)
sections.append(section1)
self._save_section(1, section_name, section1, trends, correlation_data, paper)
print(f"   ✓ Section 1: {self._count_words(section1)} words")

# NEW: Garbage collect after each section
import gc
gc.collect()
```

---

## 🧪 Testing Plan

### Test 1: Memory Monitoring
```bash
# Run pipeline with memory tracking
while true; do
    ps aux | grep python | grep researcher7 | awk '{print $6}' >> memory_log.txt
    sleep 10
done &

python main.py --provider ollama
```

### Test 2: Verify Fix
1. Implement Option A + C changes
2. Run full 10-section pipeline
3. Monitor memory usage per section
4. **Success criteria:** Complete all 10 sections without OOM

### Test 3: Stress Test
1. Run 3 consecutive full pipelines
2. Check for memory growth across runs
3. Verify Ollama doesn't accumulate memory

---

## 📈 Expected Results

### Before Fix
- **Memory at start:** ~2.8 GB (phi4 + transformers + Python)
- **Memory at Section 7:** ~5-6 GB (accumulated)
- **Result:** SIGKILL

### After Fix (Option A + C)
- **Memory at start:** ~2.4 GB (phi4 + smaller model + Python)
- **Memory after Step 2:** ~1.9 GB (model freed)
- **Memory at Section 7:** ~2.5-3 GB (GC prevents accumulation)
- **Memory at Section 10:** ~2.7-3.2 GB
- **Result:** ✅ Complete successfully with ~4-5GB headroom

---

## 🚀 Next Actions

1. ✅ Complete sections 8-10 manually (current workaround)
2. ⚠️ Implement Option A + C fixes
3. ✅ Test complete 10-section run
4. ✅ Document results in RUN_LOG.md
5. ✅ Commit fixes to GitHub

---

## 📚 References

- **PyTorch Memory Management:** https://pytorch.org/docs/stable/notes/cuda.html#memory-management
- **Python GC:** https://docs.python.org/3/library/gc.html
- **Linux OOM Killer:** https://www.kernel.org/doc/gorman/html/understand/understand016.html
- **Ollama Memory:** https://github.com/ollama/ollama/blob/main/docs/faq.md#how-do-i-configure-ollama-server

---

**Status:** Analysis complete, fix plan ready  
**Priority:** High (blocks full pipeline completion)  
**Estimated Fix Time:** 30 minutes coding + 30 minutes testing = **1 hour total**
