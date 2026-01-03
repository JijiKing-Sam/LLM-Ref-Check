#!/bin/bash
# 启动 Streamlit Web 界面

# 激活 conda 环境（如果使用）
# conda activate your_env

# 启动 Streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
