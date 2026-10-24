#!/bin/bash
cd /root/autodl-tmp/ar_20261024/agents/ar_20261024_gpu11/workspace/repo
export CUDA_VISIBLE_DEVICES=1
export HF_HOME=/root/autodl-tmp/cache/huggingface
export HF_HUB_OFFLINE=1
export TORCH_HOME=/root/autodl-tmp/cache/torch
echo $$ > /root/autodl-tmp/ar_20261024/agents/ar_20261024_gpu11/workspace/train.pid
/root/autodl-tmp/envs/ar/bin/python train.py > /root/autodl-tmp/ar_20261024/agents/ar_20261024_gpu11/workspace/train_exp_gq_weight_decay_hi_seed43.stdout 2> /root/autodl-tmp/ar_20261024/agents/ar_20261024_gpu11/workspace/train_exp_gq_weight_decay_hi_seed43.stderr
echo "EXIT=$?" > /root/autodl-tmp/ar_20261024/agents/ar_20261024_gpu11/workspace/train.exitcode
