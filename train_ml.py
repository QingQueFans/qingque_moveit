#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/diyuanqiongyu/qingfu_moveit')

from moveit_bootstrap import init_moveit_paths
init_moveit_paths()

from kin_ik.ik_solver import IKSolver

ik = IKSolver()
if hasattr(ik, 'train_ml_model'):
    success = ik.train_ml_model()
    print(f"训练结果: {'✅成功' if success else '❌失败，需要更多数据'}")
else:
    print("❌ 没有 train_ml_model 方法")
