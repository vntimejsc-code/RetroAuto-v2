import os

# --- CẤU HÌNH ---
# Tên file kết quả đầu ra
OUTPUT_FILENAME = "FULL_PROJECT_CONTEXT.txt"

# Các đuôi file muốn gộp (thêm .js, .html, .css nếu cần)
ALLOWED_EXTENSIONS = {'.py', '.ini', '.json', '.yaml', '.md'}

# Các thư mục muốn BỎ QUA (rất quan trọng để file không bị rác)
IGNORE_DIRS = {
    '.git', '__pycache__', 'venv', 'env', '.idea', '.vscode', 
    'build', 'dist', 'migrations', 'node_modules'
}

def merge_files():
    root_dir = os.getcwd() # Lấy thư mục hiện tại
    
    # Mở file kết quả để ghi (encoding utf-8)
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as outfile:
        
        # Viết phần mở đầu cho AI hiểu context
        outfile.write(f"PROJECT SOURCE CODE SUMMARY\n")
        outfile.write(f"This file contains the merged source code of the project.\n")
        outfile.write(f"Structure: Header with filename -> File Content -> Separator\n\n")

        file_count = 0
        
        # Duyệt qua tất cả thư mục và file
        for dirpath, dirnames, filenames in os.walk(root_dir):
            
            # 1. Lọc bỏ các thư mục không mong muốn (sửa trực tiếp list dirnames)
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
            
            for filename in filenames:
                # Bỏ qua chính file script này và file output
                if filename in ['merge_project.py', OUTPUT_FILENAME]:
                    continue
                
                # 2. Kiểm tra đuôi file
                ext = os.path.splitext(filename)[1].lower()
                if ext in ALLOWED_EXTENSIONS:
                    full_path = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(full_path, root_dir)
                    
                    try:
                        # Đọc nội dung file con
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            content = infile.read()
                            
                            # 3. Ghi tiêu đề rõ ràng cho từng file (CỰC QUAN TRỌNG VỚI AI)
                            outfile.write("\n" + "="*60 + "\n")
                            outfile.write(f"START OF FILE: {relative_path}\n")
                            outfile.write("="*60 + "\n")
                            
                            # Ghi nội dung
                            outfile.write(content)
                            outfile.write("\n\n") # Thêm dòng trống cuối file
                            
                            print(f"Đã gộp: {relative_path}")
                            file_count += 1
                            
                    except Exception as e:
                        print(f"Lỗi khi đọc file {relative_path}: {e}")

    print(f"\n--- HOÀN TẤT ---")
    print(f"Đã gộp {file_count} files vào: {OUTPUT_FILENAME}")
    print(f"File này đã sẵn sàng để upload cho AI.")

if __name__ == "__main__":
    merge_files()