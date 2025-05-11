import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments
import requests
from bs4 import BeautifulSoup

# 1. 数据获取模块（从维基百科获取内容示例）
def fetch_training_data(query="Artificial Intelligence", max_length=5000):
    url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = ' '.join([p.get_text() for p in soup.find_all('p')])
    return text[:max_length]

# 2. 数据处理模块
def prepare_data(text, tokenizer, block_size=128):
    with open("dataset.txt", "w") as f:
        f.write(text)
    
    dataset = TextDataset(
        tokenizer=tokenizer,
        file_path="dataset.txt",
        block_size=block_size
    )
    
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    return dataset, data_collator

# 3. Transformer模型定义
class AIChatModel:
    def __init__(self, model_name="gpt2"):
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        self.model = GPT2LMHeadModel.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token  # 设置填充标记

    def train(self, dataset, data_collator, epochs=3):
        training_args = TrainingArguments(
            output_dir="./results",
            num_train_epochs=epochs,
            per_device_train_batch_size=2,
            save_steps=500,
            logging_dir='./logs',
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=dataset,
        )

        trainer.train()
    
    def generate_response(self, input_text, max_length=100):
        inputs = self.tokenizer.encode(input_text, return_tensors="pt")
        outputs = self.model.generate(
            inputs,
            max_length=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            top_k=50,
            top_p=0.95,
            temperature=0.7
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

# 4. 训练与使用示例
if __name__ == "__main__":
    # 初始化模型
    ai_model = AIChatModel()
    
    # 获取训练数据
    training_text = fetch_training_data()
    
    # 准备训练数据
    dataset, collator = prepare_data(training_text, ai_model.tokenizer)
    
    # 微调模型
    ai_model.train(dataset, collator, epochs=3)
    
    # 交互测试
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        response = ai_model.generate_response(user_input)
        print(f"AI: {response}")
