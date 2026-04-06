#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试运行器：运行所有测试并生成报告
"""
import os
import sys
import unittest
import time
from io import StringIO

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ColoredTextTestResult(unittest.TextTestResult):
    """带颜色输出的测试结果类"""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.success_count = 0
        self._verbosity = verbosity
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        if self._verbosity > 1:
            self.stream.write(f"\033[92m✓ {test._testMethodName}\033[0m\n")
    
    def addError(self, test, err):
        super().addError(test, err)
        if self._verbosity > 1:
            self.stream.write(f"\033[91m✗ {test._testMethodName} (ERROR)\033[0m\n")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self._verbosity > 1:
            self.stream.write(f"\033[91m✗ {test._testMethodName} (FAIL)\033[0m\n")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self._verbosity > 1:
            self.stream.write(f"\033[93m- {test._testMethodName} (SKIP)\033[0m\n")


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.test_modules = [
            'test_basic_functionality',
            'test_knowledge_base_manager', 
            'test_file_import',
            'test_api_endpoints',
            'test_error_handling',
            'test_performance',
            'test_zhipu_basic',
            'test_zhipu_integration',
            'test_integration'
        ]
        self.results = {}
    
    def run_single_test(self, module_name):
        """运行单个测试模块"""
        print(f"\n{'='*60}")
        print(f"运行测试模块: {module_name}")
        print(f"{'='*60}")
        
        try:
            # 动态导入测试模块
            module = __import__(module_name)
            
            # 创建测试套件
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            
            # 运行测试
            stream = StringIO()
            runner = unittest.TextTestRunner(
                stream=stream,
                verbosity=2,
                resultclass=ColoredTextTestResult
            )
            
            start_time = time.time()
            result = runner.run(suite)
            end_time = time.time()
            
            # 记录结果
            self.results[module_name] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped),
                'success': result.success_count if hasattr(result, 'success_count') else result.testsRun - len(result.failures) - len(result.errors),
                'duration': end_time - start_time,
                'output': stream.getvalue()
            }
            
            # 打印结果摘要
            self.print_module_summary(module_name, self.results[module_name])
            
            return result
            
        except Exception as e:
            print(f"\033[91m导入或运行测试模块 {module_name} 时出错: {e}\033[0m")
            self.results[module_name] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'success': 0,
                'duration': 0,
                'output': str(e)
            }
            return None
    
    def print_module_summary(self, module_name, result):
        """打印模块测试摘要"""
        total = result['tests_run']
        success = result['success']
        failures = result['failures']
        errors = result['errors']
        skipped = result['skipped']
        duration = result['duration']
        
        print(f"\n模块 {module_name} 测试结果:")
        print(f"  总计: {total}")
        print(f"  \033[92m成功: {success}\033[0m")
        if failures > 0:
            print(f"  \033[91m失败: {failures}\033[0m")
        if errors > 0:
            print(f"  \033[91m错误: {errors}\033[0m")
        if skipped > 0:
            print(f"  \033[93m跳过: {skipped}\033[0m")
        print(f"  耗时: {duration:.2f} 秒")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\033[94m" + "="*80)
        print("开始运行所有测试")
        print("="*80 + "\033[0m")
        
        overall_start = time.time()
        
        for module_name in self.test_modules:
            self.run_single_test(module_name)
        
        overall_end = time.time()
        
        # 打印总体报告
        self.print_overall_report(overall_end - overall_start)
    
    def print_overall_report(self, total_duration):
        """打印总体测试报告"""
        print(f"\n\033[94m{'='*80}")
        print("测试总体报告")
        print(f"{'='*80}\033[0m")
        
        total_tests = sum(r['tests_run'] for r in self.results.values())
        total_success = sum(r['success'] for r in self.results.values())
        total_failures = sum(r['failures'] for r in self.results.values())
        total_errors = sum(r['errors'] for r in self.results.values())
        total_skipped = sum(r['skipped'] for r in self.results.values())
        
        print(f"总测试数: {total_tests}")
        print(f"\033[92m成功: {total_success}\033[0m")
        if total_failures > 0:
            print(f"\033[91m失败: {total_failures}\033[0m")
        if total_errors > 0:
            print(f"\033[91m错误: {total_errors}\033[0m")
        if total_skipped > 0:
            print(f"\033[93m跳过: {total_skipped}\033[0m")
        print(f"总耗时: {total_duration:.2f} 秒")
        
        # 成功率
        if total_tests > 0:
            success_rate = (total_success / total_tests) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        # 各模块详细结果
        print(f"\n各模块详细结果:")
        print(f"{'模块名':<30} {'测试数':<8} {'成功':<6} {'失败':<6} {'错误':<6} {'耗时(s)':<10}")
        print("-" * 80)
        
        for module_name, result in self.results.items():
            print(f"{module_name:<30} {result['tests_run']:<8} {result['success']:<6} {result['failures']:<6} {result['errors']:<6} {result['duration']:<10.2f}")
        
        # 失败和错误详情
        if total_failures > 0 or total_errors > 0:
            print(f"\n\033[91m失败和错误详情:\033[0m")
            for module_name, result in self.results.items():
                if result['failures'] > 0 or result['errors'] > 0:
                    print(f"\n{module_name}:")
                    print(result['output'])
    
    def run_specific_tests(self, test_names):
        """运行指定的测试"""
        print(f"\033[94m运行指定测试: {', '.join(test_names)}\033[0m")
        
        for test_name in test_names:
            if test_name in self.test_modules:
                self.run_single_test(test_name)
            else:
                print(f"\033[91m未找到测试模块: {test_name}\033[0m")
        
        if self.results:
            total_duration = sum(r['duration'] for r in self.results.values())
            self.print_overall_report(total_duration)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='运行测试套件')
    parser.add_argument('--tests', nargs='*', help='指定要运行的测试模块')
    parser.add_argument('--list', action='store_true', help='列出所有可用的测试模块')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.list:
        print("可用的测试模块:")
        for module in runner.test_modules:
            print(f"  - {module}")
        return
    
    if args.tests:
        runner.run_specific_tests(args.tests)
    else:
        runner.run_all_tests()


if __name__ == "__main__":
    main()