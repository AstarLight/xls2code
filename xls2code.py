#author	: lijunshi2015@163.com 
#create	: 2021-03-21

from jinja2 import Template
import xlrd, sys, os, time
import traceback

render_time = 0
TEMPL = {}

# 配置页固定格式
CONF_CONST = [
		["Z_name", "STRING"], #第一行，表名字
		["Z_desc", "STRING"], # 第二行，表的描述说明

		# 额外配置
		# 列1：
		# 	不检查编号的唯一性:
		["Z_ex_conf", "INT"], # 第三行，额外配置

		["Z_template_sum", "INT"], 			# 这个必须放在最后， 第四行，输出的文件数目
		]

# 生成文件行的配置 ， 对应第五行
GEN_FILE_CONF = [
		["template_name", "STRING", ],    #模板名字
		["mode", "STRING", ],                # 模式
		["code", "STRING", ],                 # 编码
		["sheet", "STRING", ],                 # 要处理的sheet名字
		["gen_file_name", "STRING", ],       # 生成输出的文件名字
		["param", "STRING", ],
		]

def get_col(s):
	col = 0
	for i in range(len(s)):
		col = col*26 + ord(s[i]) - ord('A') + 1
	return col - 1

def _UGLY_FLOAT(val):
	if type(val) == float:
		if val == int(val):
			val = int(val)
	return val
	
def V(sh,r,c):
	if r >= sh.nrows:
		return ""
	else:
		if type(c) == int:
			v = sh.cell_value(r,c)
			v = _UGLY_FLOAT(v)
			return v
		elif type(c) == str:
			return _UGLY_FLOAT(sh.cell_value(r,get_col(c)))
		else:
			pass
	
def VT(v):
	try:	# unicode 在 str() 的时候可能出错, 所以 try 一下
		if type(v) == unicode:
			return v
		else:
			return str(v)
	except:
		return v
	
FORBID_CHAR = [ u"，", u"：", u"。" ]
def VS(v):
	return v
    
# 读取xls文档里的sheet
def get_sheets(xlspath):
	try:
		book = xlrd.open_workbook(xlspath)
	except:
		#print "can't open file: %s" % xlspath
		# sys.exit(1)
		raise Exception("can't open file: %s" % xlspath)
	else:
		return book.sheets()

def get_sheet_by_name(xlspath, sheetname):
	try:
		book = xlrd.open_workbook(xlspath)
	except:
		print ("can't open file: %s" % xlspath)
		sys.exit(1)

	for x in range(book.nsheets):
		sh = book.sheet_by_index(x)
		if sh.name == sheetname:
			return sh

	return None
	
def read_grid(sh, r, c):
	return VS(V(sh,r,c))

# 读取CONFIG表schema
def read_file_config(filepath):
	sh_conf = { "Z_template" : [], "Z_ex_data":{} }
	sh_name = ""
	sh_start = 0
	sh = get_sheet_by_name(filepath, "CONFIG")
	for row in range(0, sh.nrows):
		if row < len(CONF_CONST): 	# 还是固定列范围，对应处理CONF_CONST
			if len(CONF_CONST[row]) > 2: 	# 有超过一项
				sh_conf[CONF_CONST[row][0]] = range(0, len(CONF_CONST[row])-1)
				for a in range(1, len(CONF_CONST[row])):
					sh_conf[CONF_CONST[row][0]][a-1] = read_grid(sh, row, a)
			else:
				sh_conf[CONF_CONST[row][0]] = read_grid(sh, row, 1)
		elif row - len(CONF_CONST) + 1<= sh_conf["Z_template_sum"]: 	# 生成文件列表，对应处理GEN_FILE_CONF
			each_sh_conf = {}
			col_size = len(GEN_FILE_CONF)
			if col_size > sh.ncols-1:
				col_size = sh.ncols-1
			for a in range(0, col_size):
				each_sh_conf[GEN_FILE_CONF[a][0]] = read_grid(sh, row, a+1)
			sh_conf["Z_template"].append(each_sh_conf)
		else: # 表单系列，处理sheet的定义
			if sh_start == 0: 	# 一张新表
				sh_start = row
				sh_name = read_grid(sh, row, 1)
				sh_conf[sh_name] = []
			else:
				col_name = read_grid(sh, row, 1)
				col_type = read_grid(sh, row, 2)
				col_no_empty = read_grid(sh, row, 3)

				if len(col_name) == 0: 	# 到一张sheet列最后一个
					sh_start = 0
				else:
					sh_conf[sh_name].append((col_name, col_type, col_no_empty))
	print(sh_conf)
	return sh_conf

# 读一行数据
def read_row_data(sh, row, sheet_struct):
	row_data = {}
	for col in range(0, len(sheet_struct)):
		t_cnt = 0
		t_cnt = V(sh, row, col)
		row_data[sheet_struct[col][0]] = t_cnt

	return row_data

# 把从xls读到的信息，导入到代码模板里
def write_file(sh_conf, data):
	write_data = { "content":data }
	print("write_data=", write_data)
	for temp in sh_conf["Z_template"]:
		global TEMPLATE_DIR
		temp_f = "./template/"+temp["template_name"]

		output_f = temp["gen_file_name"]
		# render by jinja2
		start_t = time.perf_counter()
		if not temp_f in TEMPL.keys():
			fo = open(temp_f)
			print(temp_f)
			#TEMPL[temp_f] = Template(fo.read().decode("gbk"))
			TEMPL[temp_f] = Template(fo.read())
			fo.close()
		print (TEMPL[temp_f])
		code = TEMPL[temp_f].render(write_data)

		global render_time
		render_time += time.perf_counter() - start_t
		manual_code = ""

		if os.path.exists(output_f):
			global tem_file
			if(temp["code"] == "gbk"):
				item_file = open(output_f, "r", encoding='gbk')
			else:
				item_file = open(output_f, "r")
			file_lines = item_file.readlines()
			item_file.close()

			for i in range(len(file_lines)-1,-1,-1):
				if file_lines[i].find("以下是手工编写部分") != -1:
					if i == len(file_lines)-1:
						break 	# 这个是最后一行
					manual_code = ''.join(file_lines[i+1:])
			
			if len(manual_code):
				code = ("%s%s"%(code, manual_code))

		if(temp["code"] == "gbk"):
			code.encode("gbk")
			item_file = open(output_f, "w+", encoding='gbk')
			print("encoding is gbk")
		else:
			item_file = open(output_f, "w+")
			
		item_file.write(code)
		item_file.close()

def parse_row(sh, sh_conf, sheet_struct, row, sheet_data):
	row_data = read_row_data(sh, row, sheet_struct)
	key_name = sheet_struct[0][0]

	if not row_data[key_name]: 	# 一般第一列都是id, 这个都没有, 估计就不用生成这行了
		return
	
	key_value = row_data[key_name]

	sheet_data[key_value] = row_data 	# 以id为索引的dict
	sheet_data["list"].append(row_data) 	# 顺序的array
	print(sheet_data)

def gen_codes(filepath):
	# 读取配置schema
	sh_conf = read_file_config(filepath)
	
	# 遍历xls里的每一张表，只处理CONFIG里指定的某些sheet
	for sh in get_sheets(filepath):
		print("sheet name=%s" %(sh.name))
		if sh.name != sh_conf["Z_template"][0]["sheet"]:
			print(sh_conf.keys())
			continue
		# 读取其它sheet的内容，并由template生成文件
		sheet_data = { "list":[] } 	# 单张表数据dict
		sheet_struct = sh_conf[sh.name]
		key_name = sheet_struct[0][0]
		for row in range(0, sh.nrows):
			# 处理首行，首行是文字解释
			if row == 0:
				for col in range(0, sh.ncols):
					print (VT(V(sh, row, col)))
			else:
				# 处理正常行
				parse_row(sh, sh_conf, sheet_struct, row, sheet_data)
				# 根据key进行一次排序
				sheet_data["list"] = sorted(sheet_data["list"], key = lambda item:item[key_name])

		#print (sheet_data)
		# 整个文件读完, 写文件(所有行生成一个文件)
		write_file(sh_conf, sheet_data)
					
		
def main():
	print ("gen_codes start %s" % (sys.argv[1]))
	global render_time
	try:
		gen_codes(sys.argv[1])
	except Exception as e:
		print ('[error] 表格%s抛出异常. %s'%(sys.argv[1], e))
		print (traceback.print_exc())
		pass
	else:
		print ("生成 %s ......time:%.2f ms" % (sys.argv[1], render_time * 1000))
		render_time = 0
		
if __name__ == "__main__":
	main()
