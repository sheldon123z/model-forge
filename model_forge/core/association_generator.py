"""
联想生成器 - 使用大模型对一类事物生成多种不同样式的prompts

功能：
- 输入一个类别(如"椅子"、"变压器")
- AI自动联想该类别下的多种不同样式、规格、用途的具体物品
- 为每个物品生成详细的3D模型描述prompt
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from ..providers.base import ChatMessage, ProviderType
from ..providers.manager import get_provider_manager, ProviderManager


class AssociationMode(str, Enum):
    """联想模式"""
    STYLE = "style"           # 不同风格样式
    SPECIFICATION = "spec"    # 不同规格参数
    PURPOSE = "purpose"       # 不同用途场景
    MATERIAL = "material"     # 不同材质
    ERA = "era"               # 不同时代
    REGION = "region"         # 不同地区
    COMPREHENSIVE = "comprehensive"  # 综合联想


@dataclass
class AssociatedItem:
    """联想生成的单个物品"""
    name: str                 # 物品名称
    description: str          # 详细描述
    prompt: str               # 3D模型生成prompt
    category: str             # 所属类别
    subcategory: str          # 子类别
    specifications: Dict[str, Any] = field(default_factory=dict)  # 规格参数
    tags: List[str] = field(default_factory=list)  # 标签


@dataclass
class AssociationResult:
    """联想生成结果"""
    category: str             # 输入的类别
    mode: AssociationMode     # 联想模式
    items: List[AssociatedItem]  # 生成的物品列表
    total_count: int          # 总数
    metadata: Dict[str, Any] = field(default_factory=dict)


class AssociationGenerator:
    """联想生成器"""

    # 联想提示词模板
    ASSOCIATION_PROMPT_TEMPLATE = """你是一个专业的3D模型设计师和产品专家。用户将提供一个物品类别，你需要联想出该类别下多种不同的具体物品。

## 任务
为类别「{category}」生成{count}个不同的具体物品描述。

## 联想模式
{mode_description}

## 要求
1. 每个物品必须是该类别的具体实例，而非抽象概念
2. 物品之间应有明显差异（形状、大小、用途、风格等）
3. 涵盖该类别的不同类型、规格、用途
4. 描述应具体、详细，便于3D建模
5. 考虑工业设计和实际应用场景

## 输出格式
以JSON数组格式输出，每个物品包含以下字段：
```json
[
  {{
    "name": "物品具体名称",
    "subcategory": "子类别",
    "description": "详细外观描述（50-100字）",
    "specifications": {{
      "尺寸": "长x宽x高",
      "材质": "主要材质",
      "颜色": "主要颜色",
      "其他参数": "根据物品类型添加"
    }},
    "tags": ["标签1", "标签2"],
    "prompt": "用于3D模型生成的英文prompt（详细描述外观、材质、角度等）"
  }}
]
```

## 示例
如果类别是"椅子"，你可能生成：
- 现代简约办公椅（旋转、网面靠背、五星脚）
- 经典木质餐椅（橡木、雕花靠背、四脚）
- 电竞游戏椅（人体工学、赛车风格、可调扶手）
- 户外折叠椅（铝合金框架、防水帆布）
- 北欧风格单人沙发椅（布艺、高脚、圆润造型）
...等等

请直接输出JSON数组，不要包含其他内容。"""

    MODE_DESCRIPTIONS = {
        AssociationMode.STYLE: "按不同设计风格联想：现代、古典、工业、简约、复古、未来、民族等",
        AssociationMode.SPECIFICATION: "按不同规格参数联想：尺寸大小、功率等级、容量、精度等",
        AssociationMode.PURPOSE: "按不同用途场景联想：家用、商用、工业、户外、医疗、教育等",
        AssociationMode.MATERIAL: "按不同材质联想：木质、金属、塑料、玻璃、陶瓷、布艺、皮革等",
        AssociationMode.ERA: "按不同时代风格联想：古代、近代、现代、未来科幻等",
        AssociationMode.REGION: "按不同地区特色联想：中式、日式、欧式、美式、北欧、地中海等",
        AssociationMode.COMPREHENSIVE: "综合考虑风格、规格、用途、材质等多个维度进行全面联想",
    }

    def __init__(
        self,
        provider_type: ProviderType = ProviderType.DEEPSEEK,
        model: Optional[str] = None,
    ):
        """
        初始化联想生成器

        Args:
            provider_type: 使用的AI服务商
            model: 使用的模型名称
        """
        self.provider_type = provider_type
        self.model = model
        self.manager = get_provider_manager()

    def generate(
        self,
        category: str,
        count: int = 20,
        mode: AssociationMode = AssociationMode.COMPREHENSIVE,
        custom_requirements: Optional[str] = None,
    ) -> AssociationResult:
        """
        为指定类别生成联想物品列表

        Args:
            category: 物品类别（如"椅子"、"变压器"、"汽车"）
            count: 生成数量（建议10-50）
            mode: 联想模式
            custom_requirements: 自定义要求

        Returns:
            联想生成结果
        """
        # 构建prompt
        mode_description = self.MODE_DESCRIPTIONS.get(mode, self.MODE_DESCRIPTIONS[AssociationMode.COMPREHENSIVE])
        if custom_requirements:
            mode_description += f"\n\n额外要求：{custom_requirements}"

        prompt = self.ASSOCIATION_PROMPT_TEMPLATE.format(
            category=category,
            count=count,
            mode_description=mode_description,
        )

        # 调用AI
        messages = [ChatMessage(role="user", content=prompt)]
        response = self.manager.chat(
            self.provider_type,
            messages,
            model=self.model,
            temperature=0.8,  # 使用较高温度增加多样性
            max_tokens=8000,
        )

        # 解析响应
        items = self._parse_response(response.content, category)

        return AssociationResult(
            category=category,
            mode=mode,
            items=items,
            total_count=len(items),
            metadata={
                "provider": self.provider_type.value,
                "model": response.model,
                "requested_count": count,
            }
        )

    async def agenerate(
        self,
        category: str,
        count: int = 20,
        mode: AssociationMode = AssociationMode.COMPREHENSIVE,
        custom_requirements: Optional[str] = None,
    ) -> AssociationResult:
        """异步生成联想物品列表"""
        mode_description = self.MODE_DESCRIPTIONS.get(mode, self.MODE_DESCRIPTIONS[AssociationMode.COMPREHENSIVE])
        if custom_requirements:
            mode_description += f"\n\n额外要求：{custom_requirements}"

        prompt = self.ASSOCIATION_PROMPT_TEMPLATE.format(
            category=category,
            count=count,
            mode_description=mode_description,
        )

        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.manager.achat(
            self.provider_type,
            messages,
            model=self.model,
            temperature=0.8,
            max_tokens=8000,
        )

        items = self._parse_response(response.content, category)

        return AssociationResult(
            category=category,
            mode=mode,
            items=items,
            total_count=len(items),
            metadata={
                "provider": self.provider_type.value,
                "model": response.model,
                "requested_count": count,
            }
        )

    def _parse_response(self, content: str, category: str) -> List[AssociatedItem]:
        """解析AI响应"""
        items = []

        # 提取JSON
        try:
            # 尝试直接解析
            data = json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    return items
            else:
                return items

        if not isinstance(data, list):
            return items

        for item_data in data:
            try:
                item = AssociatedItem(
                    name=item_data.get("name", "未命名"),
                    description=item_data.get("description", ""),
                    prompt=item_data.get("prompt", ""),
                    category=category,
                    subcategory=item_data.get("subcategory", ""),
                    specifications=item_data.get("specifications", {}),
                    tags=item_data.get("tags", []),
                )
                items.append(item)
            except Exception:
                continue

        return items

    def generate_for_industry(
        self,
        industry: str,
        equipment_type: str,
        count: int = 20,
    ) -> AssociationResult:
        """
        针对特定行业生成设备联想

        Args:
            industry: 行业（如"电力"、"制造"、"建筑"）
            equipment_type: 设备类型（如"变压器"、"电机"、"泵"）
            count: 生成数量

        Returns:
            联想结果
        """
        custom_req = f"""
专注于{industry}行业的{equipment_type}设备，需要考虑：
1. 不同电压/功率等级
2. 不同应用场景（室内/室外、高温/低温等）
3. 不同品牌特点和外观风格
4. 不同年代的设计（老旧设备、现代设备、未来概念）
5. 相关配套设备和组件
"""
        return self.generate(
            category=f"{industry}{equipment_type}",
            count=count,
            mode=AssociationMode.COMPREHENSIVE,
            custom_requirements=custom_req,
        )


class CategorySuggester:
    """类别建议器 - 帮助用户发现可联想的类别"""

    # 预定义的类别库
    CATEGORY_LIBRARY = {
        "电力设备": [
            "变压器", "断路器", "隔离开关", "电流互感器", "电压互感器",
            "避雷器", "电容器", "电抗器", "母线", "绝缘子",
            "配电箱", "开关柜", "电缆", "电杆", "铁塔",
        ],
        "制造设备": [
            "数控机床", "工业机器人", "输送带", "压力机", "注塑机",
            "焊接设备", "切割机", "磨床", "车床", "铣床",
            "3D打印机", "激光设备", "检测仪器", "包装机", "码垛机",
        ],
        "家具": [
            "椅子", "桌子", "沙发", "床", "柜子",
            "书架", "茶几", "餐桌", "衣柜", "鞋柜",
            "办公桌", "会议桌", "吧台", "梳妆台", "电视柜",
        ],
        "交通工具": [
            "汽车", "卡车", "公交车", "摩托车", "自行车",
            "火车", "地铁", "飞机", "直升机", "船",
            "叉车", "挖掘机", "起重机", "拖拉机", "电动滑板车",
        ],
        "建筑结构": [
            "住宅", "办公楼", "工厂", "仓库", "体育馆",
            "桥梁", "隧道", "水塔", "烟囱", "信号塔",
            "停车场", "加油站", "变电站", "水处理厂", "发电厂",
        ],
        "电子设备": [
            "手机", "电脑", "平板", "显示器", "键盘",
            "路由器", "服务器", "机柜", "传感器", "摄像头",
            "音箱", "耳机", "电视", "投影仪", "打印机",
        ],
        "医疗设备": [
            "CT机", "MRI", "X光机", "超声设备", "心电图机",
            "手术台", "病床", "轮椅", "呼吸机", "监护仪",
            "注射泵", "输液架", "消毒柜", "药柜", "急救车",
        ],
        "厨房设备": [
            "冰箱", "烤箱", "微波炉", "洗碗机", "油烟机",
            "燃气灶", "电饭煲", "咖啡机", "榨汁机", "搅拌机",
            "厨具架", "切菜机", "蒸箱", "保温柜", "制冰机",
        ],
    }

    @classmethod
    def get_categories(cls, industry: Optional[str] = None) -> Dict[str, List[str]]:
        """获取类别库"""
        if industry:
            return {industry: cls.CATEGORY_LIBRARY.get(industry, [])}
        return cls.CATEGORY_LIBRARY

    @classmethod
    def search_category(cls, keyword: str) -> List[str]:
        """搜索相关类别"""
        results = []
        keyword = keyword.lower()
        for industry, categories in cls.CATEGORY_LIBRARY.items():
            if keyword in industry.lower():
                results.extend(categories)
            else:
                results.extend([c for c in categories if keyword in c.lower()])
        return list(set(results))
