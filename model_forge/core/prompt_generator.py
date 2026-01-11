"""
Enhanced Prompt Generator - 使用高级Prompt工程技术生成高质量3D模型提示词

支持多行业、多领域的通用3D模型生成，融合以下技术：
- Few-shot Learning (动态示例选择)
- Chain-of-Thought Prompting (链式思维)
- Self-Verification (自我验证)
- Meta-Prompting (元提示优化)
- Progressive Disclosure (渐进式细节)
"""

import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from google import genai


class IndustryDomain(str, Enum):
    """支持的行业领域"""
    POWER_GRID = "power_grid"           # 电力系统
    MANUFACTURING = "manufacturing"      # 制造业
    ARCHITECTURE = "architecture"        # 建筑
    AUTOMOTIVE = "automotive"            # 汽车
    AEROSPACE = "aerospace"              # 航空航天
    MEDICAL = "medical"                  # 医疗设备
    ROBOTICS = "robotics"                # 机器人
    FURNITURE = "furniture"              # 家具
    ELECTRONICS = "electronics"          # 电子设备
    GENERAL = "general"                  # 通用


class RenderStyle(str, Enum):
    """渲染风格"""
    PHOTOREALISTIC = "photorealistic"    # 照片级真实
    INDUSTRIAL = "industrial"            # 工业风格
    PRODUCT = "product"                  # 产品展示
    TECHNICAL = "technical"              # 技术图纸风格
    ARTISTIC = "artistic"                # 艺术风格
    MINIMAL = "minimal"                  # 简约风格


@dataclass
class PromptConfig:
    """提示词生成配置"""
    domain: IndustryDomain = IndustryDomain.GENERAL
    style: RenderStyle = RenderStyle.PHOTOREALISTIC
    use_few_shot: bool = True
    use_chain_of_thought: bool = True
    use_self_verification: bool = True
    optimize_iterations: int = 1
    language: str = "en"  # 输出语言: en/zh


class PromptGenerator:
    """
    高级 Prompt 生成器

    使用先进的Prompt工程技术，将用户描述转换为高质量的图像生成提示词。
    支持多行业领域，自动适配不同场景。
    """

    # 领域特定的知识库
    DOMAIN_KNOWLEDGE = {
        IndustryDomain.POWER_GRID: {
            "keywords": ["transformer", "circuit breaker", "insulator", "busbar", "switchgear", "substation"],
            "materials": ["porcelain", "steel", "copper", "aluminum", "SF6 gas", "mineral oil"],
            "colors": ["gray", "industrial blue", "safety yellow", "porcelain brown", "copper orange"],
            "components": ["high-voltage bushings", "cooling fins", "tap changers", "grounding systems"],
        },
        IndustryDomain.MANUFACTURING: {
            "keywords": ["CNC machine", "assembly line", "robotic arm", "conveyor", "press machine"],
            "materials": ["steel", "aluminum", "plastic", "rubber", "composite"],
            "colors": ["industrial gray", "safety orange", "machine green", "warning yellow"],
            "components": ["control panels", "hydraulic systems", "servo motors", "safety guards"],
        },
        IndustryDomain.ARCHITECTURE: {
            "keywords": ["building", "facade", "interior", "furniture", "structure"],
            "materials": ["concrete", "glass", "wood", "steel", "marble", "brick"],
            "colors": ["natural wood", "white", "concrete gray", "glass blue", "warm tones"],
            "components": ["windows", "doors", "columns", "beams", "railings"],
        },
        IndustryDomain.AUTOMOTIVE: {
            "keywords": ["car", "vehicle", "engine", "chassis", "suspension"],
            "materials": ["carbon fiber", "aluminum", "leather", "plastic", "glass"],
            "colors": ["metallic silver", "glossy black", "racing red", "electric blue"],
            "components": ["wheels", "headlights", "dashboard", "seats", "exhaust"],
        },
        IndustryDomain.AEROSPACE: {
            "keywords": ["aircraft", "satellite", "rocket", "drone", "turbine"],
            "materials": ["titanium", "carbon composite", "aluminum alloy", "ceramic"],
            "colors": ["aerospace white", "metallic silver", "carbon black", "accent orange"],
            "components": ["wings", "fuselage", "engines", "landing gear", "cockpit"],
        },
        IndustryDomain.MEDICAL: {
            "keywords": ["MRI", "surgical robot", "prosthetic", "diagnostic", "implant"],
            "materials": ["surgical steel", "titanium", "medical-grade plastic", "silicone"],
            "colors": ["clinical white", "soft blue", "medical green", "sterile gray"],
            "components": ["displays", "sensors", "articulated arms", "sterile surfaces"],
        },
        IndustryDomain.ROBOTICS: {
            "keywords": ["robot", "actuator", "gripper", "sensor", "controller"],
            "materials": ["aluminum", "carbon fiber", "engineering plastic", "rubber"],
            "colors": ["industrial white", "accent orange", "tech black", "safety yellow"],
            "components": ["joints", "motors", "cameras", "end effectors", "cables"],
        },
        IndustryDomain.FURNITURE: {
            "keywords": ["chair", "table", "sofa", "cabinet", "shelf"],
            "materials": ["solid wood", "fabric", "leather", "metal", "glass"],
            "colors": ["natural oak", "walnut brown", "white lacquer", "matte black"],
            "components": ["legs", "armrests", "cushions", "drawers", "handles"],
        },
        IndustryDomain.ELECTRONICS: {
            "keywords": ["device", "circuit", "display", "sensor", "module"],
            "materials": ["plastic", "aluminum", "glass", "PCB", "silicon"],
            "colors": ["tech black", "silver aluminum", "white minimalist", "accent colors"],
            "components": ["screens", "buttons", "ports", "antennas", "heatsinks"],
        },
        IndustryDomain.GENERAL: {
            "keywords": ["object", "product", "item", "model", "design"],
            "materials": ["various materials appropriate for the object"],
            "colors": ["realistic colors appropriate for the object"],
            "components": ["relevant parts and features"],
        },
    }

    # Few-shot 示例库
    FEW_SHOT_EXAMPLES = [
        {
            "input": "一台工业机器人手臂",
            "domain": IndustryDomain.ROBOTICS,
            "output": """A 6-axis industrial robotic arm, photorealistic 3D render.

Main body: Streamlined white and orange housing with smooth curved surfaces, approximately 1.2 meters reach.

Joints: Six articulated joints with visible servo motor housings, black rubber cable management channels running along the arm.

End effector: Pneumatic parallel gripper with aluminum fingers and rubber grip pads.

Base: Heavy-duty steel mounting plate with cable pass-through and emergency stop button.

Materials: Powder-coated aluminum body, engineering plastic covers, anodized aluminum joints.

Camera: Three-quarter front view, 45-degree elevation
Lighting: Soft studio lighting with subtle rim light
Background: Clean gradient, light gray to white
Style: Industrial product photography, sharp focus, no motion blur"""
        },
        {
            "input": "一个现代简约风格的办公椅",
            "domain": IndustryDomain.FURNITURE,
            "output": """A modern minimalist ergonomic office chair, photorealistic 3D render.

Seat and back: Breathable black mesh fabric stretched over curved aluminum frame, ergonomic lumbar support integrated.

Armrests: Height-adjustable 4D armrests with soft-touch polyurethane pads, brushed aluminum stems.

Base: 5-star polished aluminum base with smooth-rolling casters, pneumatic height adjustment cylinder.

Headrest: Adjustable mesh headrest with aluminum mounting bracket.

Dimensions: Standard office chair proportions, approximately 120cm total height.

Materials: High-quality mesh fabric, die-cast aluminum, engineering plastic components.

Camera: Three-quarter view showcasing ergonomic curves
Lighting: Soft diffused studio lighting, subtle shadows
Background: Pure white seamless
Style: Product catalog photography, clean and professional"""
        },
        {
            "input": "220kV油浸式电力变压器",
            "domain": IndustryDomain.POWER_GRID,
            "output": """A 220kV oil-immersed power transformer, industrial photorealistic 3D render.

Main tank: Large rectangular steel tank with corrugated cooling fins on sides, painted industrial gray. Dimensions approximately 8m x 4m x 5m height.

High-voltage bushings: Three tall porcelain bushings (brown/tan color) on top, with metal caps and arcing horns, approximately 2.5m height each.

Low-voltage bushings: Smaller porcelain bushings on the side, with connection terminals.

Cooling system: Oil-filled radiator banks with fans, pipe connections visible.

Accessories: Buchholz relay, oil level indicator, temperature gauges, pressure relief valve on top.

Foundation: Concrete pad with oil containment berm, grounding connections visible.

Materials: Painted steel tank, glazed porcelain insulators, copper/aluminum conductors.

Camera: Three-quarter front view, eye level with slight elevation
Lighting: Outdoor natural lighting, overcast sky feel
Background: Industrial substation environment or clean gradient
Style: Technical industrial photography, sharp details, accurate proportions"""
        },
    ]

    # 风格提示词模板
    STYLE_TEMPLATES = {
        RenderStyle.PHOTOREALISTIC: "photorealistic 3D render, physically accurate materials, realistic lighting and shadows",
        RenderStyle.INDUSTRIAL: "industrial photography style, technical accuracy, sharp focus, professional lighting",
        RenderStyle.PRODUCT: "product photography, studio lighting, clean background, commercial quality",
        RenderStyle.TECHNICAL: "technical illustration style, clear details, cutaway views where appropriate, precise proportions",
        RenderStyle.ARTISTIC: "artistic 3D render, stylized materials, dramatic lighting, creative composition",
        RenderStyle.MINIMAL: "minimalist 3D render, clean lines, simple materials, soft shadows, elegant composition",
    }

    # 元提示：用于生成提示词的提示词
    META_PROMPT_TEMPLATE = """You are an expert prompt engineer specializing in generating prompts for AI image generation systems, particularly for 3D model visualization.

## Your Task
Analyze the user's description and generate a highly detailed, structured prompt that will produce an accurate, high-quality 3D model image.

## Chain of Thought Process
Follow this reasoning process step by step:

### Step 1: Object Analysis
- What is the main subject/object?
- What category/domain does it belong to?
- What are the key defining characteristics?

### Step 2: Component Breakdown
- List all major components/parts
- Describe each component's appearance, material, and position
- Note any unique features or details

### Step 3: Material & Color Specification
- What materials make up each component?
- What are the realistic colors for this object?
- Consider surface finishes (matte, glossy, textured)

### Step 4: Scale & Proportion
- What are the approximate dimensions?
- How do components relate to each other in size?

### Step 5: Camera & Composition
- What viewing angle best showcases this object?
- What background complements it?

### Step 6: Lighting & Style
- What lighting setup creates the best result?
- What rendering style is most appropriate?

{domain_context}

{few_shot_section}

## User Description
{description}

{additional_context}

## Output Format
Generate your response in exactly this format:

ANALYSIS:
[Your step-by-step reasoning following the chain of thought above]

PROMPT:
[The complete, detailed image generation prompt in English]

NEGATIVE:
[A list of things to avoid in the image]

CONFIDENCE:
[Your confidence level: HIGH/MEDIUM/LOW and brief explanation]"""

    VERIFICATION_PROMPT = """Review this image generation prompt and verify it meets quality standards:

PROMPT TO VERIFY:
{prompt}

VERIFICATION CHECKLIST:
1. ✓ Clear subject identification
2. ✓ Detailed component descriptions
3. ✓ Specific materials and colors
4. ✓ Proper scale/proportions mentioned
5. ✓ Camera angle specified
6. ✓ Lighting described
7. ✓ Style/mood indicated
8. ✓ No conflicting instructions

If any issues are found, provide an IMPROVED version.
If the prompt is good, respond with "VERIFIED: PASS" and the original prompt.

VERIFICATION RESULT:"""

    def __init__(self, api_key: str, config: PromptConfig = None):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
        self.config = config or PromptConfig()

    def _detect_domain(self, description: str) -> IndustryDomain:
        """自动检测描述所属的行业领域"""
        description_lower = description.lower()

        # 检测关键词匹配
        domain_scores = {}
        for domain, knowledge in self.DOMAIN_KNOWLEDGE.items():
            if domain == IndustryDomain.GENERAL:
                continue
            score = sum(1 for kw in knowledge["keywords"] if kw in description_lower)
            # 也检查中文关键词
            cn_keywords = {
                IndustryDomain.POWER_GRID: ["变压器", "断路器", "绝缘子", "母线", "开关", "电力", "电网", "kv", "kV"],
                IndustryDomain.MANUFACTURING: ["机床", "数控", "生产线", "流水线", "冲压"],
                IndustryDomain.ARCHITECTURE: ["建筑", "房屋", "室内", "装修", "设计"],
                IndustryDomain.AUTOMOTIVE: ["汽车", "车辆", "发动机", "底盘", "轮胎"],
                IndustryDomain.AEROSPACE: ["飞机", "卫星", "火箭", "无人机", "航空"],
                IndustryDomain.MEDICAL: ["医疗", "手术", "诊断", "植入", "假肢"],
                IndustryDomain.ROBOTICS: ["机器人", "机械臂", "自动化", "伺服"],
                IndustryDomain.FURNITURE: ["椅子", "桌子", "沙发", "柜子", "家具"],
                IndustryDomain.ELECTRONICS: ["电子", "电路", "显示器", "手机", "设备"],
            }
            if domain in cn_keywords:
                score += sum(1 for kw in cn_keywords[domain] if kw in description)
            domain_scores[domain] = score

        # 返回得分最高的领域
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain

        return IndustryDomain.GENERAL

    def _get_few_shot_section(self, domain: IndustryDomain) -> str:
        """获取Few-shot示例部分"""
        if not self.config.use_few_shot:
            return ""

        # 选择相关示例
        relevant_examples = [ex for ex in self.FEW_SHOT_EXAMPLES if ex["domain"] == domain]
        if not relevant_examples:
            relevant_examples = self.FEW_SHOT_EXAMPLES[:2]  # 使用通用示例

        examples_text = "\n\n## Reference Examples\nHere are examples of well-structured prompts:\n\n"
        for i, ex in enumerate(relevant_examples[:2], 1):
            examples_text += f"### Example {i}\n**Input:** {ex['input']}\n**Output:**\n{ex['output']}\n\n"

        return examples_text

    def _get_domain_context(self, domain: IndustryDomain) -> str:
        """获取领域特定的上下文"""
        knowledge = self.DOMAIN_KNOWLEDGE.get(domain, self.DOMAIN_KNOWLEDGE[IndustryDomain.GENERAL])

        return f"""## Domain Knowledge ({domain.value})
- Common keywords: {', '.join(knowledge['keywords'][:5])}
- Typical materials: {', '.join(knowledge['materials'][:5])}
- Standard colors: {', '.join(knowledge['colors'][:5])}
- Key components: {', '.join(knowledge['components'][:5])}"""

    def _build_meta_prompt(self, description: str, domain: IndustryDomain,
                           equipment_type: str = None, additional_params: dict = None) -> str:
        """构建元提示词"""
        domain_context = self._get_domain_context(domain)
        few_shot_section = self._get_few_shot_section(domain)
        style_hint = self.STYLE_TEMPLATES.get(self.config.style, self.STYLE_TEMPLATES[RenderStyle.PHOTOREALISTIC])

        additional_context = ""
        if equipment_type:
            additional_context += f"\n- Equipment Type: {equipment_type}"
        if additional_params:
            additional_context += f"\n- Additional Parameters: {json.dumps(additional_params, ensure_ascii=False)}"
        additional_context += f"\n- Target Style: {style_hint}"

        if additional_context:
            additional_context = "## Additional Context" + additional_context

        return self.META_PROMPT_TEMPLATE.format(
            domain_context=domain_context,
            few_shot_section=few_shot_section,
            description=description,
            additional_context=additional_context
        )

    def _verify_prompt(self, prompt: str) -> str:
        """使用自我验证改进提示词"""
        if not self.config.use_self_verification:
            return prompt

        verification_prompt = self.VERIFICATION_PROMPT.format(prompt=prompt)

        response = self.client.models.generate_content(
            model=self.model,
            contents=verification_prompt
        )

        result = response.text

        # 如果验证通过，返回原始提示词
        if "VERIFIED: PASS" in result:
            return prompt

        # 否则提取改进版本
        if "IMPROVED" in result or "improved" in result.lower():
            # 尝试提取改进的提示词
            lines = result.split('\n')
            improved_start = False
            improved_prompt = []
            for line in lines:
                if 'improved' in line.lower() or improved_start:
                    improved_start = True
                    improved_prompt.append(line)
            if improved_prompt:
                return '\n'.join(improved_prompt[1:]).strip()

        return prompt

    def generate(self, description: str,
                 equipment_type: str = None,
                 voltage_level: str = None,
                 domain: IndustryDomain = None,
                 style: RenderStyle = None,
                 additional_params: dict = None) -> dict:
        """
        生成高质量的3D模型图像提示词

        Args:
            description: 用户的对象描述（支持中英文）
            equipment_type: 设备/对象类型（可选）
            voltage_level: 电压等级（仅电力设备，可选）
            domain: 行业领域（可选，自动检测）
            style: 渲染风格（可选）
            additional_params: 额外参数（可选）

        Returns:
            包含 prompt, negative_prompt, analysis, confidence 的字典
        """
        # 自动检测或使用指定的领域
        detected_domain = domain or self._detect_domain(description)

        # 临时更新配置
        if style:
            self.config.style = style

        # 处理电力设备特殊参数
        if voltage_level:
            if additional_params is None:
                additional_params = {}
            additional_params["voltage_level"] = voltage_level

        # 构建元提示词
        meta_prompt = self._build_meta_prompt(
            description=description,
            domain=detected_domain,
            equipment_type=equipment_type,
            additional_params=additional_params
        )

        # 调用 LLM 生成提示词
        response = self.client.models.generate_content(
            model=self.model,
            contents=meta_prompt
        )

        result_text = response.text

        # 解析响应
        analysis = ""
        prompt = ""
        negative_prompt = "cartoon, anime, stylized, low quality, blurry, deformed, unrealistic proportions, bad anatomy"
        confidence = "MEDIUM"

        # 提取各部分
        if "ANALYSIS:" in result_text:
            parts = result_text.split("PROMPT:")
            analysis = parts[0].replace("ANALYSIS:", "").strip()
            if len(parts) > 1:
                remaining = parts[1]
                if "NEGATIVE:" in remaining:
                    prompt_neg = remaining.split("NEGATIVE:")
                    prompt = prompt_neg[0].strip()
                    neg_conf = prompt_neg[1]
                    if "CONFIDENCE:" in neg_conf:
                        neg_conf_parts = neg_conf.split("CONFIDENCE:")
                        negative_prompt = neg_conf_parts[0].strip()
                        confidence = neg_conf_parts[1].strip()
                    else:
                        negative_prompt = neg_conf.strip()
                else:
                    prompt = remaining.strip()
        elif "PROMPT:" in result_text:
            parts = result_text.split("PROMPT:")
            prompt = parts[1].split("NEGATIVE:")[0].strip() if len(parts) > 1 else result_text
        else:
            prompt = result_text.strip()

        # 清理
        prompt = prompt.replace("```", "").strip()
        negative_prompt = negative_prompt.replace("```", "").strip()

        # 自我验证和改进
        if self.config.use_self_verification and self.config.optimize_iterations > 0:
            for _ in range(self.config.optimize_iterations):
                prompt = self._verify_prompt(prompt)

        return {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "analysis": analysis,
            "confidence": confidence,
            "detected_domain": detected_domain.value,
            "style": self.config.style.value,
            "raw_response": result_text
        }

    def optimize_prompt(self, prompt: str, feedback: str = None) -> dict:
        """
        优化已有的提示词

        Args:
            prompt: 要优化的提示词
            feedback: 用户反馈（可选）

        Returns:
            优化后的提示词
        """
        optimize_prompt = f"""You are a prompt optimization expert. Improve this image generation prompt.

ORIGINAL PROMPT:
{prompt}

{f'USER FEEDBACK: {feedback}' if feedback else ''}

OPTIMIZATION GOALS:
1. Add more specific details where vague
2. Improve material and lighting descriptions
3. Ensure proper camera angle specification
4. Add any missing structural details
5. Make colors more specific
6. Ensure proportions are mentioned

OUTPUT the improved prompt only, no explanations:"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=optimize_prompt
        )

        return {
            "original_prompt": prompt,
            "optimized_prompt": response.text.strip(),
            "feedback_applied": feedback is not None
        }
