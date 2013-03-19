import imaplib, email, pickle, re, os
import imap_auth

mailBoxQuery = "ALL"
#can be set to anything in the IMAP standard
#mailBoxQuery = '(TO "listserv@listserv.com")'

def buildEmailDatabase():
    if not os.path.exists("data"):
        os.makedirs("data")
    (user_name,auth_string) = imap_auth.makeIMAPAuthString()
    imap_conn = imaplib.IMAP4_SSL('imap.gmail.com')
    imap_conn.debug = 4
    imap_conn.authenticate('XOAUTH2', lambda x: auth_string)
    imap_conn.select('INBOX')
    #This is the search query to execute to access all of the listserv emails
    result, data = imap_conn.uid("search",None,mailBoxQuery)
    listOfEmails = data[0].split()
    emailDatabase = {}
    try:
        f = open("data/"+user_name,"r")
        emailDatabase = pickle.load(f)    
        f.close()
    except IOError:
        print "No email file found, will create one"
    #mapping function
    newDatabase = {}
    for emailUID in listOfEmails:
        if emailUID in emailDatabase:
            newDatabase[emailUID] = emailDatabase[emailUID]
            continue
        result, data = imap_conn.uid('fetch', emailUID, '(X-GM-THRID X-GM-MSGID RFC822)')
        parsedEmail = email.message_from_string(data[0][1])
        #create a small version of the email
        parsedIds = re.findall("(?<=X-GM-THRID )\d+|(?<=X-GM-MSGID )\d+",data[0][0])
        emailData = {
            "uid":emailUID,
            "threadid":parsedIds[0],
            "msgid":parsedIds[1],
            "from":parsedEmail["from"],
            "subject":parsedEmail["subject"],
            "date":parsedEmail["date"],
            "content":[]
            }
        if parsedEmail.get_content_maintype() == 'multipart':
            for part in parsedEmail.get_payload():
                #only print the plaintext messages
                if part.get_content_type() == 'text/plain':
                    emailData["content"].append(part.get_payload())
        elif parsedEmail.get_content_maintype() == 'text':
            emailData["content"].append(parsedEmail.get_payload())

        emailDatabase[emailUID] = emailData
        newDatabase[emailUID] = emailData
    f = open("data/"+user_name,"w")
    pickle.dump(emailDatabase,f)
    f.close()
    imap_conn.shutdown()
    return newDatabase
