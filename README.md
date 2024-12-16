# HuffmanArchiver
`HuffmanArchiver` - это простой и готовый инструмент для сжатия файлов

## Алгоритм
Алгоритм кодирования Хаффмана (1952 год) позволяет эффективно сжимать 
данные путем замены более часто встречающихся символов более короткими 
кодами и реже встречающихся символов более длинными кодами.

## Формат архива
![Imgur](https://i.imgur.com/5s3oYg5.png)
## Формат записей блока 'Файл'
![Imgur](https://i.imgur.com/V9ErGiV.png)

## Шифрование
Для симметричного шифрования используем MD5 для хэшируемых данных. Для шифрования данных используется стандарт AES.

## Флаги запуска
```
usage: main.py [-h] [-c] [-d] [-b] [-t] [-p] input_path output_path

Huffman archiver

positional arguments:
  input_path        Путь к файлу/директории
  output_path       Путь для сохранения архива/разархивированных данных

options:
  -h, --help        show this help message and exit
  -c, --compress    Операция сжатия
  -d, --decompress  Операция распаковки
  -b, --bin         Сжатие в бинарном виде
  -t, --text        Сжатие текстовых данных
  -p, --protect     Установка защиты на файлы
```

### Примеры
Сжатие файла или директории с текстовыми данными:
```
sudo python3 main.py -c -t <path_file_or_dir> <path_output_dir>
```
Распаковка архива:
```
sudo python3 main.py -d <path_archive_file> <path_output_dir>
```
Сжатие файла или директории с бинарными данными с паролями:
```
sudo python3 main.py -c -b -p <path_file_or_dir> <path_output_dir>
```

### Пример
![imgur](https://i.imgur.com/8eIntTl.png)
