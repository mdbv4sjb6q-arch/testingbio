# llama_wrapper.py - llama.cpp本地LLM包装
"""
dmind-trading-merged本地LLM集成
使用llama.cpp运行本地量化模型
"""

import subprocess
import json
import os
import sys
from typing import Optional, Dict, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class LlamaLocal:
    """本地llama.cpp LLM包装类"""
    
    def __init__(self, 
                 model_path: str = "/Users/tonychan/Documents/trae_projects/AI/core/dmind-trading-merged/dmind-trading-q4_k_m.gguf",
                 llama_cpp_path: str = "./core/llama.cpp/build/bin/llama-cli",
                 n_ctx: int = 2048,
                 n_gpu_layers: int = 100,
                 verbose: bool = False):
        """
        初始化本地LLM
        
        Args:
            model_path: GGUF模型路径
            llama_cpp_path: llama.cpp可执行文件路径
            n_ctx: 上下文长度
            n_gpu_layers: GPU加速层数
            verbose: 是否输出详细信息
        """
        self.model_path = model_path
        self.llama_cpp_path = llama_cpp_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose
        
        # 验证文件存在
        if not Path(model_path).exists():
            logger.error(f"Model file not found: {model_path}")
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        if not Path(llama_cpp_path).exists():
            logger.warning(f"llama.cpp not found at {llama_cpp_path}")
            logger.warning("使用Python llama-cpp-python库作为备选方案")
    
    def use_python_backend(self):
        """使用Python llama-cpp-python库"""
        try:
            from llama_cpp import Llama
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=self.verbose
            )
            logger.info("Using llama-cpp-python backend")
            return True
        except ImportError:
            logger.error("llama-cpp-python not installed")
            logger.info("Install with: pip install llama-cpp-python")
            return False
    
    def generate(self, 
                prompt: str,
                max_tokens: int = 512,
                temperature: float = 0.5,
                top_p: float = 0.8,
                top_k: int = 30) -> Dict[str, str]:
        """
        生成文本
        
        Args:
            prompt: 提示文本
            max_tokens: 最大token数
            temperature: 温度（降低以获得更确定的回复）
            top_p: nucleus采样
            top_k: top-k采样
            
        Returns:
            {'text': 生成的文本, 'tokens': token数}
        """
        try:
            # 尝试使用Python库
            if hasattr(self, 'llm'):
                output = self.llm(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    echo=False
                )
                text = output['choices'][0]['text'].strip()
                # 清理LLM输出中的元数据和提示词
                text = self._clean_response(text)
                return {
                    'text': text,
                    'tokens': output['usage']['completion_tokens']
                }
            
            # 回退到命令行
            cmd = [
                self.llama_cpp_path,
                '-m', self.model_path,
                '-p', prompt,
                '-n', str(max_tokens),
                '--temp', str(temperature),
                '--top-p', str(top_p),
                '--top-k', str(top_k),
                '--no-display-prompt',
            ]
            
            if self.n_gpu_layers > 0:
                cmd.extend(['-ngl', str(self.n_gpu_layers)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"llama.cpp error: {result.stderr}")
                return {'text': '', 'tokens': 0}
            
            return {
                'text': result.stdout.strip(),
                'tokens': len(result.stdout.split())
            }
        
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return {'text': '', 'tokens': 0}
    
    def chat(self,
            messages: List[Dict[str, str]],
            max_tokens: int = 512,
            temperature: float = 0.5) -> str:
        """
        聊天接口 - 改进版，输出自然的回复
        
        Args:
            messages: 消息列表 [{'role': 'system', 'content': '...'}, {'role': 'user', 'content': '...'}, ...]
            max_tokens: 最大token数
            temperature: 温度 (降低以获得更确定的回复)
            
        Returns:
            回复文本
        """
        # 格式化为聊天提示
        prompt = self._format_chat_prompt(messages)
        
        result = self.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return result['text']
    
    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """格式化聊天消息为提示词 - 正确处理system角色"""
        system_content = ""
        conversation = ""
        
        # 分离system消息和对话消息
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                system_content = content
            elif role == 'user':
                conversation += f"用户: {content}\n"
            elif role == 'assistant':
                conversation += f"助手: {content}\n"
        
        # 构建完整提示词: system + 对话历史 + 等待助手回复
        prompt = system_content + "\n\n" + conversation + "助手: "
        return prompt
    
    def _clean_response(self, text: str) -> str:
        """
        清理LLM输出，去除重复、提示词和不必要的文本
        """
        import re
        
        # ============ 第一步：删除"用户回复: "及其后面的所有内容 ============
        if '用户回复: ' in text:
            text = text.split('用户回复: ')[0]
        
        # ============ 第二步：删除"用户问题"及其后面的所有内容 ============
        if '用户问题' in text:
            text = text.split('用户问题')[0]
        
        # ============ 第三步：删除"用户:"及其后面的所有内容 ============
        if '用户:' in text:
            text = text.split('用户:')[0]
        
        # ============ 第四步：删除所有提示词和系统指令（防止泄露） ============
        # 删除"你是一位专业的投资顾问AI"及之后的所有系统指令
        if '是一位专业的投资顾问AI' in text:
            text = text.split('是一位专业的投资顾问AI')[0]
        
        # 删除其他常见的系统提示词
        prompt_patterns = [
            r"你是.*?AI.*?\n.*?回复应该.*?(?:\n|$)",  # 你是...AI的模式
            r"你的回复应该：.*?自然流畅.*?(?:\n\n|$)",  # 回复指南
            r"你必须.*?(?:\n|$)",  # 必须...
            r"你正在分析.*?(?:\n\n|$)",  # 分析指令
            r"你的任务：.*?(?:\n\n|$)",  # 任务说明
            r"关于\S+的问题：",  # 移除"关于XXX的问题："前缀
        ]
        
        for pattern in prompt_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)
        
        # 去除重复的句子/段落（同一句话出现2次以上）
        lines = text.split('\n')
        seen_lines = set()
        unique_lines = []
        
        for line in lines:
            line_clean = line.strip()
            if line_clean:
                # 检查是否已看过类似的行
                if line_clean not in seen_lines:
                    seen_lines.add(line_clean)
                    unique_lines.append(line)
            else:
                # 保留空行但只保留一次
                if not unique_lines or unique_lines[-1].strip() != '':
                    unique_lines.append(line)
        
        text = '\n'.join(unique_lines)
        
        # 去除常见的思考框架
        patterns_to_remove = [
            r"^.*?(?:好的、核心要点来了|我将从多个维度|接下来细化内容|最后检查点).*?\n+",
            r"(?:特别要注意|重要提示|需求：).*?\n*",
            r"(?:✓|✗|→|●).*?(?:\)|\n)",
        ]
        
        cleaned = text
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.MULTILINE)
        
        # 从第一个有意义的句子开始
        lines = cleaned.strip().split('\n')
        result = []
        started = False
        
        for line in lines:
            line = line.strip()
            # 跳过开头的元数据和提示
            if not started:
                # 寻找第一个有意义的句子（包含数据、建议、分析等关键词）
                if any(kw in line for kw in ['建议', '应该', '可以', '不建议', '高', '低', '目标', '风险', '关键', '分析', '趋势', '信号', '支撑', '阻力', '做多', '做空', '买入', '卖出']):
                    started = True
            
            if started and line and len(line) > 2:
                # 不是单字符回复
                result.append(line)
        
        final_text = '\n'.join(result).strip()
        
        # 如果最后清理后的文本太短或为空，返回原始文本的前500个字符
        if not final_text or len(final_text) < 10:
            return text[:500].strip()
        
        return final_text
    
    def analyze_market(self, 
                      symbol: str,
                      current_price: float,
                      indicators: Dict,
                      news: Optional[str] = None) -> str:
        """
        分析市场 - 专用投资分析接口
        
        Args:
            symbol: 标的代码
            current_price: 当前价格
            indicators: 技术指标
            news: 相关新闻
            
        Returns:
            分析结果
        """
        prompt = f"""你是一个专业的投资分析师。分析以下市场信息：

标的代码: {symbol}
当前价格: ${current_price}

技术指标:
- 5日均线 (MA1): {indicators.get('ma1', 'N/A')}
- 10日均线 (MA2): {indicators.get('ma2', 'N/A')}
- 20日均线 (MA3): {indicators.get('ma3', 'N/A')}
- 60日均线 (MA4): {indicators.get('ma4', 'N/A')}
- 波段指标VAR3: {indicators.get('var3', 'N/A')}
- 波段指标VAR4: {indicators.get('var4', 'N/A')}
- KDJ-X: {indicators.get('xx', 'N/A')}
- KDJ-Y: {indicators.get('yy', 'N/A')}
- CCI: {indicators.get('cci', 'N/A')}

买卖信号:
- 买点: {indicators.get('buy', False)}
- 卖点: {indicators.get('sell', False)}

相关新闻: {news or '无'}

请提供：
1. 当前趋势判断 (上升/下降/震荡)
2. 建议操作 (现货买入，合约做多/现货卖出，合约做空)
3. 目标价格范围
4. 现货买入和合约做多对应的跌到多少就要止损和涨到多少就要止盈/现货卖出和合约做空对应的涨到多少就要止损和跌到多少就要止盈
5. 风险提示和免责声明

分析:"""
        
        return self.generate(prompt, max_tokens=1024)['text']


# 全局LLM实例
_llm_instance = None

def get_llm() -> LlamaLocal:
    """获取全局LLM实例"""
    global _llm_instance
    
    if _llm_instance is None:
        _llm_instance = LlamaLocal()
        # 尝试使用Python库
        if not _llm_instance.use_python_backend():
            logger.warning("Using command-line backend")
    
    return _llm_instance

def initialize_llm(model_path: str = "/Users/tonychan/Documents/trae_projects/AI/core/dmind-trading-merged/dmind-trading-q4_k_m.gguf"):
    """初始化LLM"""
    global _llm_instance
    _llm_instance = LlamaLocal(model_path=model_path)
    _llm_instance.use_python_backend()
