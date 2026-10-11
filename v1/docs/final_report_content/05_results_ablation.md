# Experiments & Results - Ablation Study

## 1. Study Design

### 1.1 Purpose

Systematically test the impact of generator count and content assessment on scale generation quality.

### 1.2 Scenario

**Collaborative Robot Assembly** (`collab_robot_assembly`)

### 1.3 Baseline Configuration

- **Item Generators**: 5 parallel generators
- **Content Assessment**: Enabled (LLM-based quality check)
- **Item Selection**: EFA/CFA statistical selection
- **Result**: 
  - Cronbach's α = 0.992
  - Cohen's d = 4.634
  - Selected items = 16

### 1.4 Ablation Variants

**Variant 1: Fewer Generators**
- **Item Generators**: 1 (vs. 5)
- **Content Assessment**: Enabled
- **Item Selection**: EFA/CFA
- **Purpose**: Test impact of generator count

**Variant 2: No Content Assessment**
- **Item Generators**: 5
- **Content Assessment**: Disabled
- **Item Selection**: Random (extreme control)
- **Purpose**: Test impact of content assessment

**Variant 3: Fewer Generators + No Content**
- **Item Generators**: 1
- **Content Assessment**: Disabled
- **Item Selection**: EFA/CFA
- **Purpose**: Test combined impact

## 2. Experimental Results

### 2.1 Results Summary

| Configuration | α | Cohen's d | Items | α Change | d Change |
|--------------|---|-----------|-------|----------|----------|
| **Baseline** | **0.992** | **4.634** | 16 | - | - |
| Fewer Generators | 0.974 | 2.194 | 14 | -1.8% | -52.7% |
| No Content (Random) | 0.966 | 2.241 | 15 | -2.6% | -51.6% |
| Fewer + No Content | 0.941 | 2.042 | 10 | -5.1% | -56.0% |

### 2.2 Key Observations

1. **All ablation variants show lower quality than baseline** ✅
2. **Internal consistency remains excellent**: All variants α > 0.94
3. **Discriminant validity decreases significantly**: All variants d < 2.5 (vs. 4.634 baseline)
4. **Combined impact is most severe**: Fewer + No Content shows largest decrease

## 3. Impact of Generator Count

### 3.1 Fewer Generators Variant

**Configuration**: 1 generator, content=True, EFA+CFA

**Results**:
- α = 0.974 (decreased 1.8%)
- Cohen's d = 2.194 (decreased 52.7%)
- Items = 14

**Analysis**:
- **Internal consistency**: Slight decrease (still excellent)
- **Discriminant validity**: Large decrease (52.7% reduction)
- **Item count**: Slightly fewer items (14 vs. 16)

**Conclusion**: Multiple generators (5 vs. 1) significantly improve discriminant validity by providing a richer candidate item pool.

### 3.2 Fewer + No Content Variant

**Configuration**: 1 generator, content=False, EFA+CFA

**Results**:
- α = 0.941 (decreased 5.1%)
- Cohen's d = 2.042 (decreased 56.0%)
- Items = 10

**Analysis**:
- **Internal consistency**: Moderate decrease (still good)
- **Discriminant validity**: Very large decrease (56.0% reduction)
- **Item count**: Fewer items (10 vs. 16)

**Conclusion**: Single generator without content assessment produces the lowest quality scales.

## 4. Impact of Content Assessment

### 4.1 No Content Assessment Variant

**Configuration**: 5 generators, content=False, random selection

**Results**:
- α = 0.966 (decreased 2.6%)
- Cohen's d = 2.241 (decreased 51.6%)
- Items = 15

**Analysis**:
- **Internal consistency**: Moderate decrease (still excellent)
- **Discriminant validity**: Large decrease (51.6% reduction)
- **Item selection**: Random selection (extreme control)

**Conclusion**: Content assessment significantly improves final scale quality by filtering and refining items before statistical selection.

### 4.2 Content Assessment Role

Content assessment performs:
1. **Quality filtering**: Removes low-quality items
2. **Wording refinement**: Improves item clarity
3. **Redundancy removal**: Identifies and removes duplicate items
4. **Scenario relevance check**: Ensures items match scenario context

**Impact**: Without content assessment, even with 5 generators, quality decreases significantly (51.6% reduction in discriminant validity).

## 5. Combined Impact Analysis

### 5.1 Fewer Generators + No Content

**Configuration**: 1 generator, content=False, EFA+CFA

**Results**:
- α = 0.941 (decreased 5.1%)
- Cohen's d = 2.042 (decreased 56.0%)
- Items = 10

**Analysis**:
- **Largest quality decrease**: Both components removed
- **Internal consistency**: Still good (α > 0.94) but lowest among variants
- **Discriminant validity**: Lowest (d = 2.042, 56.0% reduction)
- **Item count**: Fewest items (10)

**Conclusion**: Both multiple generators and content assessment are essential for high-quality scale generation.

### 5.2 Component Importance Ranking

Based on impact on discriminant validity:

1. **Multiple Generators**: 52.7% impact (Fewer Generators variant)
2. **Content Assessment**: 51.6% impact (No Content variant)
3. **Combined**: 56.0% impact (Fewer + No Content variant)

**Note**: The combined impact (56.0%) is greater than either individual component, but not additive, suggesting some interaction effects.

## 6. Design Validation

### 6.1 Baseline Configuration Validation

The ablation study successfully validates our design choices:

✅ **Multiple Generators Essential**: 5 generators produce significantly better results than 1
✅ **Content Assessment Essential**: Content assessment significantly improves quality
✅ **Statistical Selection Important**: EFA/CFA selection better than random
✅ **Combined Approach Optimal**: Baseline configuration (5 + content + EFA) performs best

### 6.2 Expected vs. Actual Results

**Expected**: All ablation variants should show lower quality than baseline
**Actual**: ✅ Confirmed - all variants show quality decrease

**Expected**: Internal consistency should remain high (α > 0.9)
**Actual**: ✅ Confirmed - all variants α > 0.94

**Expected**: Discriminant validity should decrease significantly
**Actual**: ✅ Confirmed - all variants d < 2.5 (vs. 4.634 baseline)

## 7. Detailed Analysis

### 7.1 Internal Consistency Analysis

| Variant | α | Change | Interpretation |
|---------|---|--------|----------------|
| Baseline | 0.992 | - | Excellent |
| Fewer Generators | 0.974 | -1.8% | Excellent |
| No Content | 0.966 | -2.6% | Excellent |
| Fewer + No Content | 0.941 | -5.1% | Excellent |

**Key Finding**: Internal consistency remains excellent (α > 0.94) across all variants, suggesting that basic item quality is maintained even without optimal configuration.

### 7.2 Discriminant Validity Analysis

| Variant | Cohen's d | Change | Interpretation |
|---------|-----------|--------|----------------|
| Baseline | 4.634 | - | Very large effect |
| Fewer Generators | 2.194 | -52.7% | Large effect |
| No Content | 2.241 | -51.6% | Large effect |
| Fewer + No Content | 2.042 | -56.0% | Large effect |

**Key Finding**: Discriminant validity decreases dramatically (50-56% reduction) when components are removed, indicating these components are critical for distinguishing empathic from non-empathic behaviors.

### 7.3 Item Count Analysis

| Variant | Items | Change |
|---------|-------|--------|
| Baseline | 16 | - |
| Fewer Generators | 14 | -2 |
| No Content | 15 | -1 |
| Fewer + No Content | 10 | -6 |

**Key Finding**: Fewer generators produce fewer candidate items, leading to fewer final selected items. Content assessment helps maintain item count by filtering quality items.

## 8. Implications

### 8.1 System Design

1. **Multiple Generators**: Essential for diverse candidate item pools
2. **Content Assessment**: Essential for item quality filtering
3. **Statistical Selection**: Important for optimal item selection
4. **Combined Approach**: All components work together for best results

### 8.2 Practical Recommendations

1. **Use 5 generators**: Provides sufficient diversity without excessive cost
2. **Enable content assessment**: Significantly improves final quality
3. **Use EFA/CFA selection**: Better than random selection
4. **Maintain all components**: Removing any component degrades quality

### 8.3 Cost-Benefit Analysis

**Baseline Configuration**:
- Cost: Higher (5 generators + content assessment)
- Quality: Highest (α = 0.992, d = 4.634)
- **Recommendation**: Use for production scales

**Reduced Configuration** (e.g., 3 generators):
- Cost: Moderate
- Quality: Likely between baseline and ablation variants
- **Recommendation**: Use for rapid prototyping

**Minimal Configuration** (1 generator, no content):
- Cost: Lowest
- Quality: Lowest (α = 0.941, d = 2.042)
- **Recommendation**: Not recommended for production

## 9. Limitations

### 9.1 Study Limitations

1. **Single Scenario**: Ablation study conducted only on factory assembly scenario
2. **Limited Variants**: Only tested extreme cases (1 vs. 5 generators, content vs. random)
3. **No Intermediate Configurations**: Did not test 2, 3, or 4 generators

### 9.2 Future Work

1. **Multi-Scenario Ablation**: Test ablation variants across all scenarios
2. **Intermediate Configurations**: Test 2, 3, 4 generators
3. **Component Interaction**: Analyze interaction effects between components
4. **Cost Optimization**: Find optimal balance between cost and quality

## 10. Conclusion

The ablation study successfully validates our design choices:

✅ **Multiple Generators**: Essential for high-quality scales
✅ **Content Assessment**: Essential for item quality
✅ **Statistical Selection**: Important for optimal selection
✅ **Combined Approach**: All components necessary for best results

The study demonstrates that removing any component significantly degrades scale quality, particularly discriminant validity, confirming the importance of our multi-component approach.
