# -*- coding: utf-8 -*-
"""
数据库与后端服务测试工具（图形界面）
原位置: scripts/db_and_backend_test_tool.py，已整合至 test/
"""
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


def test_mysql(host, port, user, password, database, result_widget):
    """测试 MySQL 连接"""
    result_widget.delete(1.0, tk.END)
    try:
        port = int(port)
    except ValueError:
        result_widget.insert(tk.END, "端口请输入数字\n")
        return
    try:
        import pymysql
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=5,
        )
        cur = conn.cursor()
        cur.execute("SELECT 1 AS ok")
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and row[0] == 1:
            result_widget.insert(tk.END, "MySQL 连接成功！\n")
            result_widget.insert(tk.END, f"  数据库: {database}\n")
        else:
            result_widget.insert(tk.END, "连接成功但 SELECT 1 结果异常\n")
    except ImportError:
        result_widget.insert(tk.END, "请先安装: pip install pymysql\n")
    except Exception as e:
        result_widget.insert(tk.END, f"连接失败: {e}\n")


def create_database(host, port, user, password, db_name, result_widget):
    """新建数据库"""
    result_widget.delete(1.0, tk.END)
    db_name = (db_name or "").strip()
    if not db_name:
        result_widget.insert(tk.END, "请填写要创建的数据库名\n")
        return
    if not re.match(r"^[a-zA-Z0-9_]+$", db_name):
        result_widget.insert(tk.END, "数据库名只能包含字母、数字和下划线\n")
        return
    try:
        port = int(port)
    except ValueError:
        result_widget.insert(tk.END, "端口请输入数字\n")
        return
    try:
        import pymysql
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connect_timeout=5,
        )
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        cur.close()
        conn.close()
        result_widget.insert(tk.END, f"数据库 '{db_name}' 创建成功（已存在则无变化）\n")
    except ImportError:
        result_widget.insert(tk.END, "请先安装: pip install pymysql\n")
    except Exception as e:
        result_widget.insert(tk.END, f"创建失败: {e}\n")


def test_server(base_url, result_widget):
    """测试后端服务是否可访问"""
    result_widget.delete(1.0, tk.END)
    url = (base_url or "").rstrip("/")
    if not url:
        result_widget.insert(tk.END, "请填写服务地址\n")
        return
    try:
        import requests
        r = requests.get(url, timeout=5)
        result_widget.insert(tk.END, f"状态码: {r.status_code}\n")
        result_widget.insert(tk.END, f"响应: {r.text[:500] if r.text else '(空)'}\n")
    except ImportError:
        result_widget.insert(tk.END, "请先安装: pip install requests\n")
    except requests.exceptions.ConnectionError:
        result_widget.insert(tk.END, "无法连接，请确认后端已启动（如 Spring Boot 8080 端口）\n")
    except Exception as e:
        result_widget.insert(tk.END, f"请求失败: {e}\n")


def main():
    root = tk.Tk()
    root.title("数据库与后端测试")
    root.geometry("520x420")
    root.resizable(True, True)

    # 数据库测试区
    db_frame = ttk.LabelFrame(root, text="MySQL 连接测试", padding=8)
    db_frame.pack(fill=tk.X, padx=10, pady=6)

    row = 0
    ttk.Label(db_frame, text="主机:").grid(row=row, column=0, sticky=tk.W, pady=2)
    host_var = tk.StringVar(value="127.0.0.1")
    ttk.Entry(db_frame, textvariable=host_var, width=16).grid(row=row, column=1, sticky=tk.W, padx=4, pady=2)
    ttk.Label(db_frame, text="端口:").grid(row=row, column=2, sticky=tk.W, padx=(12,0), pady=2)
    port_var = tk.StringVar(value="3306")
    ttk.Entry(db_frame, textvariable=port_var, width=6).grid(row=row, column=3, sticky=tk.W, padx=4, pady=2)
    row += 1
    ttk.Label(db_frame, text="用户:").grid(row=row, column=0, sticky=tk.W, pady=2)
    user_var = tk.StringVar(value="root")
    ttk.Entry(db_frame, textvariable=user_var, width=16).grid(row=row, column=1, sticky=tk.W, padx=4, pady=2)
    ttk.Label(db_frame, text="密码:").grid(row=row, column=2, sticky=tk.W, padx=(12,0), pady=2)
    pass_var = tk.StringVar(value="1234")
    ttk.Entry(db_frame, textvariable=pass_var, width=12, show="*").grid(row=row, column=3, sticky=tk.W, padx=4, pady=2)
    row += 1
    ttk.Label(db_frame, text="数据库:").grid(row=row, column=0, sticky=tk.W, pady=2)
    db_var = tk.StringVar(value="fwwb")
    ttk.Entry(db_frame, textvariable=db_var, width=20).grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=4, pady=2)
    row += 1
    db_result = scrolledtext.ScrolledText(db_frame, height=3, width=58, state=tk.NORMAL)
    db_result.grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=4)
    row += 1
    ttk.Button(
        db_frame, text="测试 MySQL 连接",
        command=lambda: test_mysql(host_var.get(), port_var.get(), user_var.get(), pass_var.get(), db_var.get(), db_result),
    ).grid(row=row, column=0, columnspan=2, pady=4)
    row += 1
    ttk.Label(db_frame, text="新数据库名:").grid(row=row, column=0, sticky=tk.W, pady=2)
    new_db_var = tk.StringVar(value="fwwb")
    ttk.Entry(db_frame, textvariable=new_db_var, width=20).grid(row=row, column=1, sticky=tk.W, padx=4, pady=2)
    ttk.Button(
        db_frame, text="新建数据库",
        command=lambda: create_database(host_var.get(), port_var.get(), user_var.get(), pass_var.get(), new_db_var.get(), db_result),
    ).grid(row=row, column=2, columnspan=2, padx=4, pady=2)
    db_frame.columnconfigure(1, weight=1)

    # 后端服务测试区
    srv_frame = ttk.LabelFrame(root, text="后端服务测试", padding=8)
    srv_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

    ttk.Label(srv_frame, text="服务地址:").grid(row=0, column=0, sticky=tk.W, pady=2)
    url_var = tk.StringVar(value="http://127.0.0.1:8080")
    ttk.Entry(srv_frame, textvariable=url_var, width=48).grid(row=0, column=1, sticky=tk.EW, padx=4, pady=2)
    srv_result = scrolledtext.ScrolledText(srv_frame, height=6, width=58, state=tk.NORMAL)
    srv_result.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=4)
    ttk.Button(
        srv_frame, text="测试后端服务",
        command=lambda: test_server(url_var.get(), srv_result),
    ).grid(row=2, column=0, columnspan=2, pady=4)
    srv_frame.columnconfigure(1, weight=1)

    root.mainloop()


if __name__ == "__main__":
    main()
