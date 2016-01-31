## Discord Storage

import pickle

## Stores Discord Twitter Bot Information
class Storage:

    
    def __init__(self):
        self.dct = self.loader()                #Dictionary of Server Information
        self.d_email = self.dct['d_email']
        self.d_pass = self.dct['d_pass']
        self.akey = self.dct['akey']
        self.asecret = self.dct['asecret']
        self.otoken = self.dct['otoken']
        self.osecret = self.dct['osecret']
        #self.mentions = self.dct['mentions']
        #self.owner = self.dct['owner']
        #self.d_key = self.dct['d_key']
        #self.loader()

    ## Initializes Server Data File
    def loader(self,fname='data.pkl'):
        try:
            pkl_file = open(fname,'rb')
            pkl_data = pickle.load(pkl_file)
            pkl_file.close()
            return pkl_data
        except:
            pkl_file = open(fname,'wb')
            dct = {'d_email':None, 'd_pass':None, 'akey':None, 'asecret':None,
                    'otoken':None, 'osecret':None, 'mentions':{}, 'owner':[], 'd_key':None}
            pickle.dump(dct,pkl_file)
            pkl_file.close()
            return dct


    ## Saves Value to Storage
    def flush(self, fname = 'data.pkl',dct = None):
        if dct == None:
            dct = self.dct
        pkl_file = open(fname,'wb')
        pickle.dump(dct,pkl_file)
        pkl_file.close()
