import os
import struct
import pickle
import tkinter as tk
from tkinter import filedialog, messagebox

# Имя файла для хранения словарей
DICT_FILE = "dict.db"

# Загрузка словарей и счетчика из файла
def load_dicts():
    if os.path.exists(DICT_FILE):
        with open(DICT_FILE, 'rb') as f:
            data = pickle.load(f)
            return data['counter'], data['coder'], data['decoder']
    return [0], {}, {}  # Счетчик как список

# Сохранение словарей и счетчика в файл
def save_dicts(counter, coder, decoder):
    with open(DICT_FILE, 'wb') as f:
        pickle.dump({'counter': counter, 'coder': coder, 'decoder': decoder}, f)

# Функция псевдосжатия
def pseudo_compress(counter, coder, decoder, value):
    if value == 0:
        return 0
    if value in coder:
        return coder[value]
    counter[0] += 1
    coder[value] = counter[0]
    decoder[counter[0]] = value
    return counter[0]

# Функция псевдораспаковки
def pseudo_decompress(decoder, value):
    if value == 0:
        return 0
    if value in decoder:
        return decoder[value]
    raise ValueError("Значение не найдено в словаре декодирования")

# Сжатие файла с сохранением оригинального имени
def compress_file():
    counter, coder, decoder = load_dicts()
    file = filedialog.askopenfilename(title="Выберите файл для сжатия")
    if file:
        original_name = os.path.basename(file)
        original_name_bytes = original_name.encode('utf-8')
        name_len = len(original_name_bytes)  # Длина в байтах
        out_file = file + ".pcomp"
        with open(out_file, 'wb') as out_f:
            # Записываем длину имени файла (4 байта)
            out_f.write(struct.pack('>I', name_len))
            # Записываем имя файла
            out_f.write(original_name_bytes)
            # Записываем сжатые данные
            with open(file, 'rb') as in_f:
                while True:
                    buff = in_f.read(3)  # Читаем 3 байта
                    if len(buff) == 0:  # Конец файла
                        break
                    if len(buff) < 3:  # Остаток (1 или 2 байта)
                        buff += b'\x00' * (3 - len(buff))  # Дополняем нулями
                    value = struct.unpack('>I', b'\x00' + buff)[0]  # Преобразуем 3 байта в число
                    compressed = pseudo_compress(counter, coder, decoder, value)
                    out_f.write(struct.pack('>I', compressed))  # Записываем как 4 байта
        save_dicts(counter, coder, decoder)
        messagebox.showinfo("Успех", f"Файл сжат в {out_file}")

# Распаковка файла с восстановлением оригинального имени
def decompress_file():
    _, _, decoder = load_dicts()
    file = filedialog.askopenfilename(title="Выберите файл для распаковки")
    if file:
        with open(file, 'rb') as in_f:
            # Читаем длину имени файла (4 байта)
            name_len_buff = in_f.read(4)
            if len(name_len_buff) != 4:
                raise ValueError("Некорректный формат сжатого файла")
            name_len = struct.unpack('>I', name_len_buff)[0]
            # Читаем оригинальное имя файла
            original_name_bytes = in_f.read(name_len)
            if len(original_name_bytes) != name_len:
                raise ValueError("Некорректный формат сжатого файла")
            original_name = original_name_bytes.decode('utf-8')
            # Формируем путь для выходного файла
            out_file = os.path.join(os.path.dirname(file), original_name)
            # Распаковываем данные
            with open(out_file, 'wb') as out_f:
                while True:
                    buff = in_f.read(4)  # Читаем 4 байта (сжатое значение)
                    if len(buff) == 0:  # Конец файла
                        break
                    if len(buff) != 4:  # Проверка корректности формата
                        raise ValueError("Некорректный формат сжатого файла")
                    compressed = struct.unpack('>I', buff)[0]  # Преобразуем в число
                    value = pseudo_decompress(decoder, compressed)  # Получаем исходное значение
                    bytes_value = struct.pack('>I', value)[1:]  # Преобразуем в 3 байта
                    out_f.write(bytes_value)  # Записываем 3 байта
        messagebox.showinfo("Успех", f"Файл распакован в {out_file}")

# Основная функция с графическим интерфейсом
def main():
    root = tk.Tk()
    root.title("Словарь 3 Байт Блоков - Словарь Вечного Сжатия")
    root.geometry("300x150")

    compress_button = tk.Button(root, text="Сжать", command=compress_file, width=20)
    compress_button.pack(pady=20)

    decompress_button = tk.Button(root, text="Расжать", command=decompress_file, width=20)
    decompress_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()