## Twitter Bot Setup

import pickle
from Storage import *

class Setup:
    def __init__(self):
        self.kdct = ['d_email','d_pass','akey','asecret','otoken','osecret','d_key']
    
    #valid input only
    def v_input(self,string,nums):
        t1 = input(string)
        while True:
            try:
                if int(t1) in range(1, nums + 1):
                    return int(t1)
                else:
                    raise ValueError
            except:
                t1 = input('Enter Valid Input: ')
                
    #first time setup
    def osetup(self):
        tstorage.d_email = input('Enter Discord Email: ')
        tstorage.d_pass = input('Enter Discord Password: ')
        tstorage.akey = input('Enter Twitter App Key: ')
        tstorage.asecret = input('Enter Twitter App Secret: ')
        tstorage.otoken = input('Enter Twitter Oauth Token: ')
        tstorage.osecret = input('Enter Twitter Oauth Secret: ')
        print('To become the Twitter Bot Owner, message the Twitter Bot with this key.')
        tstorage.d_key = input('Enter your Owner Key: ')
        
    #modify individual setup items
    def nsetup(self):
        selection = self.v_input(('Enter the number of your choice to modify:\n'
                                '1 - Discord Email\n'
                                '2 - Discord Password\n'
                                '3 - Twitter App Key\n'
                                '4 - Twitter App Secret\n'
                                '5 - Twitter Oauth Token\n'
                                '6 - Twitter Oauth Secret\n'
                                '7 - Owner Key\n'
                                '8 - Exit setup file\n'),8)
        while selection != 8:
            selection = self.lst[selection - 1]
            tstorage.dct[selection] = input('Input Value: ')
            selection = self.v_input('Successful! Next Item? ',8)

            
            

def main():
    #no comment
    print('### Twitter Bot Setup File ###')
    
    tstorage = Storage()
    tstorage.loader()
    tsetup = Setup()
    
    if tstorage.d_email == None or tstorage.akey == None:
        tsetup.osetup()
    elif tsetup.v_input('Enter 1 to modify all values or 2 to change specific values: ',2) == 1:
        tsetup.osetup()
    else:
        tsetup.nsetup()
        
    tstorage.flush(dct)
    
    ## Writes to File
    input('Completed - Enter to Quit ')

if __name__ == "__main__":
    main()
