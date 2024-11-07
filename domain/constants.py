
# ImageAttribute = {
#     "code"": string;
#     "name"": string,
#     "colour"": string,
#     "show"": boolean
#     details?": ImageAttributeDetail[]
# }; 

#  attributeColour = {
#     "BG"": "#000000",
#     "CATHETER"": "#FFCC32",
#     "CBD"": "#99FF32",
#     "CHD"": "#4CFF32",
#     "CYSTIC_DUCT"": "#32FF65",
#     "DUODENUM"": "#32FFB2",
#     "FILLING_DEFECTS"": "#32FFFF",
#     "LHD"": "#3265FF",
#     "RAHD"": "#9932FF",
#     "RPHD"": "#FF32CC"
# }

ATTR_MAP = {
    "0": {"code":'BG', "name":'Background', "colour":'#000000', "show":True, "url":''},
    "1": {"code":'CATHETER', "name":'Cholangiogram Catheter',"colour": '#01ffcc', "show":True, "url":''},
    "2": {"code":'CBD', "name":'Common Bile Duct', "colour":'#320099', "show":True, "url":''},
    "3": {"code":'CHD', "name":'Common Hepatic duct', "colour":'#ff3200', "show":True, "url":''},
    "4": {"code":'CYSTIC_DUCT', "name":'Cystic duct', "colour":'#4cff31', "show":True, "url":''},
    "5": {"code":'DUODENUM', "name":'Duodenum (with contrast)', "colour":'#0032ff', "show":True, "url":''},
    "6": {"code":'FILLING_DEFECTS', "name":'Filling defect', "colour":'#650131', "show":True, "url":''},
    "7": {"code":'LHD', "name":'Left hepatic duct', "colour":'#ffb101', "show":True, "url":''},
    "8": {"code":'RAHD', "name":'Right anterior hepatic duct', "colour":'#33feff', "show":True, "url":''},
    "9": {"code":'RHD', "name":'Right hepatic duct', "colour":'#003264', "show":True, "url":''},
    "10": {"code":'RPHD', "name":'Right posterior hepatic duct', "colour":'#FF0098', "show":True, "url":''}
}

