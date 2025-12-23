#!/usr/bin/env python3
"""
为文章的每个二级标题生成《纽约客》风格配图
重构版：使用统一的共享配图引擎 + Claude API智能分析
"""
import re
import os
import sys
from pathlib import Path
import anthropic

# 添加共享库路径
shared_lib_path = str(Path.home() / '.codex' / 'skills' / 'shared-lib')
sys.path.insert(0, shared_lib_path)

from image_api import ImageGenerator


def parse_h2_sections(markdown_path):
    """
    解析markdown中的所有H2标题及其对应内容

    返回: [(h2_title, content, line_number), ...]
    """
    with open(markdown_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    sections = []
    current_h2 = None
    current_content = []
    current_line_num = 0

    for i, line in enumerate(lines, 1):
        # 匹配H2标题: ## 标题
        h2_match = re.match(r'^##\s+(.+)$', line.strip())

        if h2_match:
            # 保存前一个section
            if current_h2:
                content_text = ''.join(current_content).strip()
                sections.append((current_h2, content_text, current_line_num))

            # 开始新的section
            current_h2 = h2_match.group(1)
            current_content = []
            current_line_num = i

        elif current_h2:
            # 遇到H1或H3则停止当前section
            if re.match(r'^#[^#]', line.strip()) or re.match(r'^###', line.strip()):
                content_text = ''.join(current_content).strip()
                sections.append((current_h2, content_text, current_line_num))
                current_h2 = None
                current_content = []
            else:
                current_content.append(line)

    # 保存最后一个section
    if current_h2:
        content_text = ''.join(current_content).strip()
        sections.append((current_h2, content_text, current_line_num))

    return sections


def analyze_section_with_llm(h2_title, content):
    """
    使用Claude API分析章节内容，生成具体的视觉描述

    Args:
        h2_title: H2标题
        content: 章节完整内容

    Returns:
        visual_description: 具体的视觉场景描述（用于生成纽约客风格配图）
    """
    try:
        # 初始化Claude客户端
        client = anthropic.Anthropic()

        # 构建提示词
        prompt = f"""你是一位擅长将抽象概念转化为视觉隐喻的插画师。

请阅读以下文章章节，提炼核心观点，然后设计一个《纽约客》风格的插画场景描述。

**章节标题**: {h2_title}

**章节内容**:
{content[:1500]}  # 限制长度避免token过多

**要求**:
1. 深入理解章节的核心观点和关键信息
2. 用简单、具象的视觉元素（物体、场景、人物动作等）来隐喻抽象概念
3. 场景描述应该简洁（50-80字），具体且富有想象力
4. 适合用钢笔墨水速写 + 黑白线条 + 朱红点缀的风格表现
5. 避免抽象指令，给出具体的视觉元素和构图

**错误示例**（太抽象）:
- "用隐喻手法表现核心主题"
- "用对比/冲突的视觉元素表现"

**正确示例**（具体场景）:
- "一座越建越高的积木塔，底部稳固但上层摇摇欲坠，旁边一座矮小但稳定的积木塔作为对比，用黑白线条和朱红点缀表现深度网络的退化困境"
- "一个登山者在崎岖山路上艰难攀登（主路径），旁边有一条笔直的索道直达山顶（快捷连接），两条路径在山顶汇合，象征残差学习的shortcuts"

请直接输出场景描述，不要额外解释:"""

        # 调用Claude API
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # 提取返回结果
        visual_description = message.content[0].text.strip()

        # 移除可能的引号
        visual_description = visual_description.strip('"').strip("'")

        print(f"✅ Claude分析完成: {h2_title}")
        print(f"   视觉描述: {visual_description[:80]}...")

        return visual_description

    except Exception as e:
        print(f"⚠️  Claude API调用失败: {e}")
        print(f"   使用备用策略...")
        # 降级到简单的启发式规则
        return analyze_section_for_visual_strategy_fallback(h2_title, content)


def analyze_section_for_visual_strategy_fallback(h2_title, content):
    """
    备用方案：简单的启发式规则
    """
    content_lower = content.lower()[:200]

    if any(word in content_lower for word in ['对比', '比较', '冲突', '问题']):
        return "用对比/冲突的视觉元素表现"
    elif any(word in content_lower for word in ['方法', '创新', '突破', '关键']):
        return "用隐喻手法表现核心主题"
    elif any(word in content_lower for word in ['实验', '结果', '数据', '表现']):
        return "用数据可视化方式表现"
    elif any(word in content_lower for word in ['影响', '应用', '扩散']):
        return "用扩散/涟漪效应表现影响力"
    elif any(word in content_lower for word in ['深层', '本质', '理解', '为什么']):
        return "用抽象概念可视化表现深层含义"
    else:
        return "用隐喻手法表现核心主题"


def insert_image_into_markdown(markdown_path, h2_title, line_number, image_path):
    """
    在H2标题后插入图片引用

    Args:
        markdown_path: markdown文件路径
        h2_title: H2标题（用于匹配）
        line_number: H2标题所在行号
        image_path: 图片相对路径
    """
    with open(markdown_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 在H2标题后添加空行和图片
    # 格式：
    # ## 标题
    #
    # ![标题](images/xxx.png)
    #
    # 正文...

    insert_pos = line_number  # H2标题的下一行

    # 检查是否已经有图片
    if insert_pos < len(lines) and lines[insert_pos].strip().startswith('!['):
        print(f"   ⚠️  图片已存在，跳过")
        return

    # 构建图片markdown
    image_md = f"\n![{h2_title}]({image_path})\n\n"

    # 插入图片
    lines.insert(insert_pos, image_md)

    # 写回文件
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def generate_illustrations_for_markdown(
    markdown_path,
    output_dir="images/illustrations",
    image_prefix="",
    provider='auto'
):
    """
    为markdown文件的所有H2标题生成《纽约客》风格配图

    Args:
        markdown_path: markdown文件路径
        output_dir: 图片输出目录（相对于markdown文件）
        image_prefix: 图片文件名前缀（如"T5_2019"）
        provider: 图片生成API ('jimeng', 'gemini', 'auto')

    Returns:
        成功生成的数量
    """
    markdown_path = Path(markdown_path)

    if not markdown_path.exists():
        print(f"❌ 文件不存在: {markdown_path}")
        return 0

    # 1. 解析H2标题
    print("\n📋 解析markdown中的H2标题...")
    sections = parse_h2_sections(str(markdown_path))

    if not sections:
        print("❌ 未找到H2标题")
        return 0

    print(f"✅ 找到 {len(sections)} 个H2标题")

    # 2. 创建输出目录
    abs_output_dir = markdown_path.parent / output_dir
    abs_output_dir.mkdir(parents=True, exist_ok=True)

    # 3. 初始化图片生成器
    generator = ImageGenerator(provider=provider)

    # 4. 为每个H2生成配图
    success_count = 0
    failed_sections = []

    for idx, (h2_title, content, line_number) in enumerate(sections, 1):
        print(f"\n[{idx}/{len(sections)}] 正在为「{h2_title}」生成配图...")

        # 生成图片文件名
        if image_prefix:
            image_filename = f"{image_prefix}_illustration_{idx}.png"
        else:
            image_filename = f"illustration_{idx}.png"

        image_output_path = abs_output_dir / image_filename
        image_relative_path = f"{output_dir}/{image_filename}"

        # 如果图片已存在，跳过
        if image_output_path.exists():
            print(f"   ✅ 图片已存在，跳过生成")
            # 仍然插入到markdown（如果还没插入）
            insert_image_into_markdown(
                str(markdown_path),
                h2_title,
                line_number,
                image_relative_path
            )
            success_count += 1
            continue

        try:
            # 使用Claude API分析内容，生成具体视觉描述
            print(f"   🤔 使用Claude分析章节内容...")
            visual_description = analyze_section_with_llm(h2_title, content)

            # 生成图片
            image_url, used_provider = generator.generate_newyorker_style(
                visual_strategy=visual_description,
                aspect_ratio='16:9',
                max_retries=3
            )

            # 保存图片
            generator.save_image(image_url, str(image_output_path))

            print(f"   ✅ 图片已保存: {image_output_path.name} (使用 {used_provider})")

            # 插入到markdown
            insert_image_into_markdown(
                str(markdown_path),
                h2_title,
                line_number,
                image_relative_path
            )
            print(f"   ✅ 已插入到markdown")

            success_count += 1

        except Exception as e:
            print(f"   ❌ 生成失败: {e}")
            failed_sections.append(h2_title)
            continue

    # 5. 总结
    print(f"\n{'='*60}")
    print(f"✨ 完成！成功生成 {success_count}/{len(sections)} 张配图")

    if failed_sections:
        print(f"\n⚠️  失败的章节：")
        for title in failed_sections:
            print(f"   - {title}")

    print(f"\n📁 图片保存在: {abs_output_dir}")
    print(f"📄 Markdown已更新: {markdown_path.name}")

    return success_count


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="为文章的每个H2标题生成《纽约客》风格配图",
        epilog="""
示例:
  python generate_illustrations.py article.md images/illustrations T5_2019
  python generate_illustrations.py article.md --provider jimeng
        """
    )

    parser.add_argument(
        'markdown_file',
        help='Markdown文件路径'
    )

    parser.add_argument(
        'output_dir',
        nargs='?',
        default='images/illustrations',
        help='图片输出目录（默认: images/illustrations）'
    )

    parser.add_argument(
        'image_prefix',
        nargs='?',
        default='',
        help='图片文件名前缀（可选）'
    )

    parser.add_argument(
        '--provider',
        choices=['jimeng', 'gemini', 'auto'],
        default='auto',
        help='图片生成API (默认: auto - 自动选择)'
    )

    args = parser.parse_args()

    generate_illustrations_for_markdown(
        markdown_path=args.markdown_file,
        output_dir=args.output_dir,
        image_prefix=args.image_prefix,
        provider=args.provider
    )


if __name__ == "__main__":
    main()
