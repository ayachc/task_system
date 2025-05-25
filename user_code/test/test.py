import concurrent.futures
import math
import time
import os

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def stress_test(max_workers):
    numbers = [112272535095293]*128  # 大质数
    
    start = time.time()
    # 改用进程池
    with concurrent.futures.ProcessPoolExecutor(max_workers) as executor:
        list(executor.map(is_prime, numbers))
    duration = time.time() - start
    
    print(f"使用 {max_workers} 进程耗时: {duration:.2f}秒")

if __name__ == '__main__':
    print(os.getpid())
    # 测试不同进程数
    for workers in [4]:
        stress_test(workers)