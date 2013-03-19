from __future__ import print_function
import email_database, json, time, re, email.utils

EMAIL_PATTERN = "[^\s<>\"]+@[^\s<>\"]+"

def main():
    f = open("emails.js","w")
    emailDatabase = email_database.buildEmailDatabase()

    # complete list of threads
    emailList = []
    threads = {}
    for k in emailDatabase:
         del emailDatabase[k]["content"]
         parsedEmail = re.search(EMAIL_PATTERN,emailDatabase[k]["from"]).group(0)
         parsedDate = email.utils.parsedate_tz(emailDatabase[k]["date"])
         timestamp = time.mktime(parsedDate[:-1])+parsedDate[-1]
         emailDatabase[k]["from"] = parsedEmail
         emailList.append(emailDatabase[k])
         try:
             threads[emailDatabase[k]["threadid"]].append((parsedEmail, timestamp, emailDatabase[k]["subject"]))
         except KeyError:
             threads[emailDatabase[k]["threadid"]] = [(parsedEmail, timestamp, emailDatabase[k]["subject"])]
             
    threadLinks = []
    #thread mappings
    for thread in threads:
        #sort thread groups based on timestamp to get the first email        
        sortedThreadEmails = sorted(threads[thread], key=lambda obj: obj[1])
        for em in range(1,len(sortedThreadEmails)):
            if sortedThreadEmails[em][0] == sortedThreadEmails[0][0]: 
                continue
            threadLinks.append({"source":sortedThreadEmails[em][0], "target":sortedThreadEmails[0][0], "subject":sortedThreadEmails[0][2]})
    print("var threadlinks = "+json.dumps(threadLinks)+";",file=f)

    #emails by date
    dateList = {}
    for em in emailList:
        date = time.mktime(time.strptime(" ".join(em["date"].split()[1:4]), "%d %b %Y"))
        date = int(date)*1000
        if date in dateList:
            dateList[date].append(em)
        else:
            dateList[date] = [em]
    print("var emailsbydate = "+json.dumps(dateList)+";",file=f)

    #email authors
    authors = [re.search(EMAIL_PATTERN,em["from"]).group(0) for em in emailList]
    print("var authors = "+json.dumps(list(set(authors)))+";",file=f)

if __name__ == "__main__":
    main()
