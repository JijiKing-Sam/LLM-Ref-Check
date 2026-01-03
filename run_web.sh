#!/bin/bash
# 启动 Streamlit Web 界面

# 激活 conda 环境（如果使用）
# conda activate /jet/home/xma8/conda_envs/cirag0

# 启动 Streamlit（增强版界面）
streamlit run app_enhanced.py --server.port 8501 --server.address 0.0.0.0

# 或使用原版界面：
# streamlit run app.py --server.port 8501 --server.address 0.0.0.0

