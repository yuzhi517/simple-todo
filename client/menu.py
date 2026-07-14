"""交互菜单 — 终端内的数字选择式操作界面。"""

import os
from client.api import TodoAPI
from client.display import print_task_list, print_search_results


def run_menu():
    """启动交互式菜单循环。"""
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print('=' * 40)
        print('     Simple Todo — 待办事项')
        print('=' * 40)
        print()

        tasks = TodoAPI.list_tasks()
        if tasks is not None:
            total = TodoAPI.list_tasks(show_all=True)
            print_task_list(tasks, total_count=len(total) if total else None)
        else:
            print('[后端连接失败，请确认服务已启动]')

        print()
        print('-' * 40)
        print('  1. 添加任务')
        print('  2. 完成任务')
        print('  3. 恢复任务（取消完成）')
        print('  4. 删除任务')
        print('  5. 搜索任务')
        print('  6. 修改优先级')
        print('  7. 查看全部（含已完成）')
        print('  8. 刷新列表')
        print('  0. 退出')
        print('-' * 40)

        choice = input('请选择操作 [0-8]: ').strip()

        if choice == '1':
            title = input('请输入任务标题: ').strip()
            if title:
                pri = input('优先级（1-5，数字越小越重要，默认1，直接回车跳过）: ').strip()
                result = None
                if pri:
                    try:
                        result = TodoAPI.add_task(title, int(pri))
                    except ValueError:
                        print('出错了: 优先级需要是一个整数')
                else:
                    result = TodoAPI.add_task(title)
                if result:
                    print(f'✓ 已经把任务 [{result["id"]}] 加到列表里了: {title}')
            else:
                print('标题不能为空，按回车键继续...')
                input()
        elif choice == '2':
            tid = input('请输入要完成的任务编号: ').strip()
            if tid:
                try:
                    result = TodoAPI.done_task(int(tid))
                    if result:
                        print(f'✓ 任务 [{result["id"]}] 的状态已经改成已完成: {result["title"]}')
                except ValueError:
                    print(f'出错了: 你给的任务编号 "{tid}" 是不对的')
        elif choice == '3':
            all_tasks = TodoAPI.list_tasks(show_all=True) or []
            print_task_list(all_tasks, show_all=True, total_count=len(all_tasks))
            print()
            tid = input('请输入要恢复的任务编号: ').strip()
            if tid:
                try:
                    task = TodoAPI.get_task(int(tid))
                    if task and task.get('done'):
                        result = TodoAPI.undone_task(int(tid))
                        if result:
                            print(f'✓ 任务 [{result["id"]}] 的状态已经改回未完成: {result["title"]}')
                    elif task and not task.get('done'):
                        print(f'编号为 [{task["id"]}] 的这条任务目前就是未完成的状态，不需要再去恢复了。')
                except ValueError:
                    print(f'出错了: 你给的任务编号 "{tid}" 是不对的')
        elif choice == '4':
            all_tasks = TodoAPI.list_tasks(show_all=True) or []
            print_task_list(all_tasks, show_all=True, total_count=len(all_tasks))
            print()
            tid = input('请输入要删除的任务编号: ').strip()
            if tid:
                try:
                    result = TodoAPI.delete_task(int(tid))
                    if result:
                        print(f'✓ 编号为 [{result["id"]}] 的任务已经被删掉了: {result["title"]}')
                except ValueError:
                    print(f'出错了: 你给的任务编号 "{tid}" 是不对的')
        elif choice == '5':
            keyword = input('请输入搜索关键词: ').strip()
            if keyword:
                results = TodoAPI.search_tasks(keyword)
                if results is not None:
                    print_search_results(results, keyword)
        elif choice == '6':
            all_tasks = TodoAPI.list_tasks(show_all=True) or []
            print_task_list(all_tasks, show_all=True, total_count=len(all_tasks))
            print()
            tid = input('请输入任务编号: ').strip()
            pri = input('请输入新的优先级（数字越小越重要）: ').strip()
            if tid and pri:
                try:
                    result = TodoAPI.set_priority(int(tid), int(pri))
                    if result:
                        print(f'✓ 任务 [{result["id"]}] 的优先级已经被修改为 {result["priority"]}: {result["title"]}')
                except ValueError:
                    print('出错了: 任务编号和优先级都需要是整数')
        elif choice == '7':
            tasks = TodoAPI.list_tasks(show_all=True)
            if tasks is not None:
                print_task_list(tasks, show_all=True, total_count=len(tasks))
        elif choice == '8':
            continue
        elif choice == '0':
            print('再见！')
            break
        else:
            print('输入有误，请重新选择')

        if choice != '8':
            print()
            input('按回车键继续...')
