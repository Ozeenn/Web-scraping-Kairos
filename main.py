"""
@author = patrick_alan
@create_date = 21/05/2022

"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import pandas as pd
import tkinter as tk
from tkinter import ttk
import os
from credentials import Credentials

class KairosScrappy():
    def __init__(self):
        self.infos = {}
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(os.getcwd() + '\Driver\chromedriver.exe', options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        self.Credentials = Credentials()
        
    def abrir_pag(self):
        self.driver.get('https://www.dimepkairos.com.br/Dimep/Account/LogOn')
        self.driver.maximize_window()
        
                
    def login(self):
        
        self.wait.until(expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="LogOnModel_UserName"]')))
        self.driver.find_element_by_xpath('//*[@id="LogOnModel_UserName"]').send_keys(self.Credentials.email)
        self.driver.find_element_by_xpath('//*[@id="LogOnModel_Password"]').send_keys(self.Credentials.passw)
        self.driver.find_element_by_xpath('//*[@id="btnFormLogin"]').click()
                
    def coletar_horas(self):
        
        self.wait.until(expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="UserProfilePedidosJustificativas"]/span')))
        self.driver.find_element_by_xpath('//*[@id="UserProfilePedidosJustificativas"]/span').click()
        
        self.wait.until(expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="SemanaApontamentos"]/div[2]')))

        for ele_num in range(7):
            data = self.driver.find_element_by_xpath(f'//*[@id="ApontID{ele_num}"]').text.replace('\n', ' ').split()
            
            if data[1] == 'sábado' or data[1] == 'domingo':
                continue
            
            while len(data) < 6:
                data.append('00:00')
            
            for element in data[2:]:
                if data[1] not in self.infos.keys():
                    self.infos[data[1]] = []
                
                self.infos[data[1]].append(element)                

    def logoff(self):
        self.driver.get('https://www.dimepkairos.com.br/Dimep/Account/LogOff')
        
    def fechar(self):
        self.driver.quit()

class Tratamentos():
    
    @staticmethod        
    def criar_dataframe(infos):
        df = pd.DataFrame(infos).transpose()
        df.insert(4, 'Primeiro turno', pd.to_timedelta(df[1] + ':00') - pd.to_timedelta(df[0] + ':00'))
        df['Primeiro turno'] = df['Primeiro turno'].astype('string')
        df['Primeiro turno'] = df['Primeiro turno'].str.replace('0 days ', '')
        df.insert(5, 'Almoco', pd.to_timedelta(df[2] + ':00') - pd.to_timedelta(df[1] + ':00'))
        df['Almoco'] = df['Almoco'].astype('string')
        df['Almoco'] = df['Almoco'].str.replace('0 days ', '')
        df.insert(6, 'Segundo turno', pd.to_timedelta(df[3] + ':00') - pd.to_timedelta(df[2] + ':00'))
        df['Segundo turno'] = df['Segundo turno'].astype('string')
        df['Segundo turno'] = df['Segundo turno'].str.replace('0 days ', '')
        df.insert(7, 'Total', pd.to_timedelta(df['Primeiro turno']) + pd.to_timedelta(df['Segundo turno']))
        df['Total'] = df['Total'].astype('string')
        df['Total'] = df['Total'].str.replace('0 days ', '')
        df['Total'] = df['Total'].apply(Tratamentos.verifica_len)
        df['Status'] = df['Total'].apply(Tratamentos.verifica_he)
        df.columns = ['H1', 'H2', 'H3', 'H4', 'Primeiro turno', 'Almoco', 'Segundo turno', 'Total', 'Status']
        df['Primeiro turno'] = df['Primeiro turno'].apply(Tratamentos.verifica_len)
        df['Almoco'] = df['Almoco'].apply(Tratamentos.verifica_len)
        df['Segundo turno'] = df['Segundo turno'].apply(Tratamentos.verifica_len)
        df['Horas normais'] = df['Total'].apply(Tratamentos.horas_normais)
        df['Horas extras'] = df['Total'].apply(Tratamentos.horas_extras)

        return df
    
    @staticmethod
    def verifica_he(hora):
        if hora == '00:00:00':
            return f'Total de horas não cadastradas.'
        elif '07:55:00' <= hora  <= '08:05:00':
            return 'Você não tem horas extras a lançar!'
        elif '07:55:00' > hora:
            return f'Você trabalhou menos do que 8 horas diárias'
        else:
            return f"Você tem horas extras a lançar!"
        
    @staticmethod
    def horas_normais(hora):
        if hora == '00:00:00':
            return '00:00'
        elif '07:55:00' > hora:
            return hora[0:5]
        else:
            return '08:00'
        
    @staticmethod
    def horas_extras(hora):
        if hora == '00:00:00':
            return '----'
        elif '07:55:00' <= hora  <= '08:05:00':
            return '----'
        else:
            return '00:' + str(round(int(hora[3:5])/ 100, 1)).split('.')[1] + '0'
    
    @staticmethod
    def verifica_len(hora):
        if len(hora) != 8:
            return '00:00:00'
        else:
            return hora
        
    @staticmethod
    def arredonda_horas(hora):
        split_hour = hora.split(':')
        return split_hour[0] + ':' + str(round(int(split_hour[1])/ 100, 1)).split('.')[1] + '0' + ':' + split_hour[2]
  
class Window():
    def __init__(self, dataframe):   
        self.root = tk.Tk()
        self.root.geometry('1825x200')
        Window.center(self.root)
        self.root.title('Kairos')
        self.dataframe = dataframe
    
    def create_window(self):
        tk.Label(self.root,text='Controle de horas Kairos').pack()
        cols = list(self.dataframe.columns)
        tv=ttk.Treeview(self.root,columns=cols,show='tree headings',height=10)
        
        for i in cols:
            tv.column(i, width=100,anchor='c')
            tv.heading(i, text=i, anchor='c')


        tv.column('Status', width=300, anchor='c')
        tv.column('Horas normais', width=100, anchor='c')
        tv.column('Horas extras', width=100, anchor='c') 
        tv.pack()
            
        for index, row in self.dataframe.iterrows():
            tv.insert("",'end',text=index,values=list(row))

    def run(self):
        self.root.mainloop()
    
    @staticmethod
    def center(win):
        win.update_idletasks()
        width = win.winfo_width()
        frm_width = win.winfo_rootx() - win.winfo_x()
        win_width = width + 2 * frm_width
        height = win.winfo_height()
        titlebar_height = win.winfo_rooty() - win.winfo_y()
        win_height = height + titlebar_height + frm_width
        x = win.winfo_screenwidth() // 2 - win_width // 2
        y = win.winfo_screenheight() // 2 - win_height // 2
        win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        win.deiconify()


if __name__ == '__main__':
    kairos_infos = KairosScrappy()

    kairos_infos.abrir_pag()
    kairos_infos.login()
    kairos_infos.coletar_horas()
    kairos_infos.logoff()
    kairos_infos.fechar()

    dataframe = Tratamentos.criar_dataframe(kairos_infos.infos)
    tela = Window(dataframe=dataframe)
    tela.create_window()
    tela.run()
        