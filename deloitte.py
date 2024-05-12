import json

file_path = '/Users/hongyizhang/Desktop/annual_report.json'

with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

processed_data = []

for i in range(40,41):
  filename = f'{i:03}.png'
  page_data = data[filename][0]
  tables = page_data['result']['tables']
  try:
    for j in range(len(tables)):
      if len(tables[j]['table_cells']) != 0:
        if j == 1 and len(tables[0]['lines']) == 1: #判断是否需要衔接上一页的表格，衔接的话只需要拓展key_index和value，还要考虑第一行和上表最后一行是不是同一行
          new_keys = [cell['text'] for cell in tables[j]['table_cells'] if cell['start_col'] == 0]
          if new_keys[0] != '' or tables[j]['table_cells'][0]['end_row'] != 0:
            #一般来说，这种情况下key会空，但53页的情况就不算，这种用end_row != 0排除，仍需要继续优化
            processed_data[-1]['key_index'].extend(new_keys)
            for row in range(tables[j]['table_rows']):
              new_row_values = [cell['text'] for cell in tables[j]['table_cells'] if cell['start_row'] == row and cell['start_col'] != 0]
              processed_data[-1]['values'].append(new_row_values)
          else:#处理两行的合并
            processed_data[-1]['key_index'].extend(new_keys[1:])#key直接从第二个加就可以了
            for k in range(len(processed_data[-1]['values'][-1])):#把上一表最后一行value的第k列和新表的第k+1个text相加
              processed_data[-1]['values'][-1][k] += tables[j]['table_cells'][k+1]['text']
            for row in range(1,tables[j]['table_rows']): #新表从第二行开始恢复正常
              new_row_values = [cell['text'] for cell in tables[j]['table_cells'] if cell['start_row'] == row and cell['start_col'] != 0]
              processed_data[-1]['values'].append(new_row_values)
        else:
          previous_lines = tables[j-1]['lines']#table的前几行，处理title和单位，有的时候单位和币种会被分成两行，但未考虑title本身有"单位"
          if "单位" in previous_lines[-1]['text']:
            unit = previous_lines[-1]['text']
            title = previous_lines[-3]['text'] if "不适用" in previous_lines[-2]['text'] else previous_lines[-2]['text']
          elif "币种" in previous_lines[-1]['text'] and "单位" not in previous_lines[-1]['text']:
            unit = previous_lines[-2]['text'] + " " + previous_lines[-1]['text']
            title = previous_lines[-4]['text'] if "不适用" in previous_lines[-3]['text'] else previous_lines[-3]['text']
          else:
            unit = ""
            title = previous_lines[-2]['text'] if "不适用" in previous_lines[-1]['text'] else previous_lines[-1]['text']
          if title == '2021年年度报告':
            previous = data[f'{(i-1):03}.png'][0]['result']['tables'][-1]['lines']
            title = previous[-3]['text'] if "不适用" in previous[-2]['text'] else previous[-2]['text']

          headers = [[] for _ in range(tables[j]['table_cells'][0]['end_row']+1)] #第一项的end_row,可以知道这个header有几行
          for cell in tables[j]['table_cells']:
            for row in range(len(headers)):
              if cell['start_row'] == row and cell['end_row'] == row:#不跨行的cell，根据宽度插入headers该行start_col的位置
                headers[row][cell['start_col']:cell['start_col']] = [cell['text']]*(cell['end_col']-cell['start_col']+1)
              elif cell['start_row'] == row and cell['end_row'] != row:
                for cellrow in range(cell['start_row'], cell['end_row']+1):
                  headers[cellrow].append(cell['text'])#把跨行的append到每行，不跨行的会自己找位置插入。相反如果先插入跨行的，会因为length不够而错位，见134页的例子


          key_indices = [cell['text'] for cell in tables[j]['table_cells'] if cell['start_col'] == 0 and cell['start_row'] > 0]#第一列除了第一行的所有


          values = []
          for row in range(tables[j]['table_cells'][0]['end_row']+1, tables[j]['table_rows']):#header下一行开始的每一行，除了第一列的所有
            row_values = [cell['text'] for cell in tables[j]['table_cells'] if cell['start_row'] == row and cell['start_col'] != 0]
            values.append(row_values)

          processed_data.append({
              'title': title,
              'unit': unit,
              'header': headers,
              'key_index': key_indices,
              'values': values
          })
  except IndexError:
        print(filename)



def clean_data(item):#把所有的\n去掉
    if isinstance(item, dict):
        return {k: clean_data(v) for k, v in item.items()}
    elif isinstance(item, list):
        return [clean_data(x) for x in item]
    elif isinstance(item, str):
        return item.replace('\n', '')  
    return item

cleaned_data = clean_data(processed_data)
print(cleaned_data)
