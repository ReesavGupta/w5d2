import json
import os
import sys

data_path = os.path.join(os.path.dirname(__file__), 'data', 'policies_templates.json')

def load_data():
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def list_items():
    data = load_data()
    for item in data:
        print(f"ID: {item['id']} | Type: {item['type']} | Title: {item.get('title', item.get('question', ''))}")

def add_item():
    data = load_data()
    item = {}
    item['id'] = input('Enter ID: ')
    item['type'] = input('Enter type (policy/template/faq): ')
    if item['type'] == 'faq':
        item['question'] = input('Enter question: ')
        item['answer'] = input('Enter answer: ')
    elif item['type'] == 'template':
        item['title'] = input('Enter template title: ')
        item['template'] = input('Enter template text (use {var} for variables): ')
    else:
        item['title'] = input('Enter policy title: ')
        item['content'] = input('Enter policy content: ')
    tags = input('Enter tags (comma separated): ')
    item['tags'] = [t.strip() for t in tags.split(',')] if tags else []
    data.append(item)
    save_data(data)
    print('Item added.')

def update_item():
    data = load_data()
    id_ = input('Enter ID of item to update: ')
    for item in data:
        if item['id'] == id_:
            print(f"Current: {item}")
            for key in item:
                if key == 'id':
                    continue
                new_val = input(f"Update {key} (leave blank to keep current): ")
                if new_val:
                    if key == 'tags':
                        item[key] = [t.strip() for t in new_val.split(',')]
                    else:
                        item[key] = new_val
            save_data(data)
            print('Item updated.')
            return
    print('Item not found.')

def delete_item():
    data = load_data()
    id_ = input('Enter ID of item to delete: ')
    new_data = [item for item in data if item['id'] != id_]
    if len(new_data) == len(data):
        print('Item not found.')
    else:
        save_data(new_data)
        print('Item deleted.')

def usage():
    print('Usage: python manage_policies.py [list|add|update|delete]')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
    else:
        cmd = sys.argv[1]
        if cmd == 'list':
            list_items()
        elif cmd == 'add':
            add_item()
        elif cmd == 'update':
            update_item()
        elif cmd == 'delete':
            delete_item()
        else:
            usage() 