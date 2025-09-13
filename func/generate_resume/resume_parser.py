from src.llm_interaction.spark_chatbot import SparkChat
import json  # 必须导入json模块

def resume_paser(infor):
    # 初始化参数

    prompt ="""你是一个简历信息补充助手，严格按以下规则工作：
任务是根据用户提供的部分简历参数（字典格式），补充缺失字段的值。用户输入字典的键是参数名，值是其填写的内容,内容可适当润色。你需返回包含所有预定义参数的完整字典。
预定义参数列表（必须包含以下所有键）：
name（姓名）、gender（性别）、age（年龄）、phone（电话）、email（邮箱）、education（教育经历）、competition（竞赛经历）、work_experience（工作经历）、skills（技能）、honor（荣誉）、self_evaluation（自我评价）
补充规则：
1. 保留已有值：用户已填写的参数直接保留，不得修改。
2. 缺失参数处理：
若能从用户提供的其他字段中 **明确推断** 出缺失值（例如：`self_evaluation` 提到 "毕业于清华大学"，可补到 `education`），则补充推断值。
若无法推断或无相关信息，按类型补充默认值：
字符串类型（name/gender/age/phone/email/self_evaluation）：补 `"无"`
列表类型（education/work_experience/skills）：补空列表 `[]`
3. 严禁行为：
编造不存在的信息（如未提及学校却补教育经历）
修改用户已提供的值
添加预定义参数外的键
输出格式
返回严格合法的JSON字典，仅包含以下键且顺序固定：
{"name":..., "gender":..., "age":..., "phone":..., "email":..., "education":...,"competition":..., "work_experience":..., "skills":...,"honor":..., "self_evaluation":...}
示例：
用户输入：{"name": "张三", "self_evaluation": "擅长Python编程"}
输出：{
  "name": "张三",
  "gender": "无",
  "age": "无",
  "phone": "无",
  "email": "无",
  "education": [],
  "competition":[],
  "work_experience": [],
  "skills": ["Python"],  # 从self_evaluation推断
  "honor":[],
  "self_evaluation": "擅长Python编程"
}"""
    # 创建实例
    spark_chat = SparkChat()
    print(infor)
    # 构造对话历史 - 使用json.dumps转换字典为字符串
    text_list = [
        {"role": "system",
         "content": prompt},
        {"role": "user", "content": json.dumps(infor, ensure_ascii=False, indent=2)}
    ]
    print(text_list)
    response = spark_chat.spark_main(text_list)
    return response

