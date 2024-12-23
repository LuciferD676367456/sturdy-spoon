import os
import subprocess
import sys
import argparse

def escape_mermaid_label(label):
    """Экранирует кавычки и недопустимые символы в узле Mermaid."""
    return label.replace('"', '\\"')

def get_git_dependencies(repo_path):
    """Извлекает зависимости из git-репозитория."""
    if not os.path.exists(os.path.join(repo_path, ".git")):
        raise ValueError(f"Путь {repo_path} не является git-репозиторием.")

    # Извлечение истории коммитов
    result = subprocess.run(
        ["git", "-C", repo_path, "log", "--name-status", "--pretty=format:%H"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ошибка выполнения git: {result.stderr}")
    
    dependencies = {}
    current_commit = None
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        if len(line.strip()) == 40:  # Хэш коммита
            current_commit = line.strip()
            dependencies[current_commit] = []
        elif current_commit:
            _, file_path = line.split(maxsplit=1)
            dependencies[current_commit].append(file_path)
    return dependencies

def generate_mermaid_graph(dependencies):
    """Генерирует Mermaid-описание графа."""
    lines = ["graph TD"]
    for commit, files in dependencies.items():
        commit = escape_mermaid_label(commit)
        for file in files:
            file = escape_mermaid_label(file)
            lines.append(f'    "{commit}" --> "{file}"')
    graph = "\n".join(lines)
    print("[DEBUG] Mermaid Graph:\n", graph)  # Отладочный вывод графа
    return graph

def save_mermaid_file(mermaid_graph, output_path):
    """Сохраняет Mermaid-граф в файл."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)  # Создаёт директории, если их нет
    with open(output_path, "w") as f:
        f.write(mermaid_graph)

def render_graph(mermaid_file, output_image, mmdc_path="mmdc"):
    """Генерирует изображение графа из Mermaid-файла."""
    result = subprocess.run(
        [mmdc_path, "-i", mermaid_file, "-o", output_image],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ошибка генерации изображения: {result.stderr}")

def main():
    parser = argparse.ArgumentParser(description="Визуализатор графа зависимостей git-репозитория.")
    parser.add_argument("repo_path", help="Путь к анализируемому репозиторию.")
    parser.add_argument("output_image", help="Путь к файлу с изображением графа зависимостей.")
    parser.add_argument("--mmdc", default="mmdc", help="Путь к программе mermaid-cli (по умолчанию 'mmdc').")
    args = parser.parse_args()

    try:
        print("[INFO] Извлечение зависимостей из git...")
        dependencies = get_git_dependencies(args.repo_path)

        print("[INFO] Генерация Mermaid-графа...")
        mermaid_graph = generate_mermaid_graph(dependencies)
        mermaid_file = os.path.splitext(args.output_image)[0] + ".mmd"
        save_mermaid_file(mermaid_graph, mermaid_file)

        print("[INFO] Генерация изображения...")
        render_graph(mermaid_file, args.output_image, args.mmdc)

        print(f"[INFO] Граф зависимостей сохранён в {args.output_image}")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
