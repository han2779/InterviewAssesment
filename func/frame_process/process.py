import random

def analyze_expression(image):
    """随机生成面部表情数据（用于测试或模拟）"""
    expression_list = ["normal", "smiling", "frowning", "surprised"]
    expression = random.choice(expression_list)

    return {
        "expression": expression,
        "is_smiling": expression == "smiling",
        "eyebrow_strength": round(random.uniform(0.0, 1.0), 2),
        "is_eye_contact": random.choice([True, False]),
        "is_frowning": expression == "frowning"
    }
