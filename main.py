import re, math, sys, time, email.utils
from curses.ascii import isdigit
sys.path.append("lib")
from multiprocessing import Pool
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import cmudict

# local files
import email_database, syllable

def main(pool):
    emailDatabase = email_database.buildEmailDatabase()    
    start_time = time.time()
    mostEmails = stat_mostEmails(pool,emailDatabase.values())
    countDatabase = {}
    print "--------------------"
    print "Most emails sent:"
    for k in mostEmails:
        print str(k[0]) + " sent " + str(k[1]) + " emails"
        #keep a database of email counts to use later for the reading level 
        countDatabase[k[0]] = k[1]
    print "-------------------"
    print "Most replied to emails"
    mostRepliedTo = stat_mostRepliedTo(pool,emailDatabase.values())    
    for k in mostRepliedTo[:20]:
        print str(k[0]) + " had " + str(k[1]) + " email replies to his/her email threads"
    mostThreads = stat_mostThreads(pool,emailDatabase.values())
    print "--------------------"
    print "Most likely to reply to an email thread"
    for k in mostThreads[:20]:
        print str(k[0]) + " has a thread reply frequency score of " + str(k[1])
    print "--------------------"
    readingLevel = stat_readingDifficulty(pool,emailDatabase.values())
    avgReadingLevel = sorted([(k[0],k[1]/countDatabase[k[0]]) for k in readingLevel], key=lambda obj : (-obj[1],obj[0]))
    print "Highest grade reading level of emails"
    for k in avgReadingLevel[:10]:
        print str(k[0]) + " averaged a score of " + str(k[1])
    print "-------------------"
    print "Lowest grade reading level of emails"
    for k in avgReadingLevel[::-1][:10]:
        print str(k[0]) + " averaged a score of " + str(k[1])
    print "-------------------"
    print "finished in "+str(time.time() - start_time)+"s"

JOB_PROCESSES = 6
EMAIL_PATTERN = "[^\s<>\"]+@[^\s<>\"]+"
'''most emails sent'''
def stat_mostEmails(pool,emaildb):
    partition = list(partitionfunc(emaildb))
    mappings = pool.map(stat_mostEmails_mapfunc, partition)
    results = reducefunc(mappings)
    return sorted(results, key=lambda obj : (-obj[1],obj[0]))
def stat_mostEmails_mapfunc(objs):
    mapping = {}
    for obj in objs:
        email = re.search(EMAIL_PATTERN,obj["from"]).group(0)
        try:
            mapping[email] +=1
        except KeyError:
            mapping[email] = 1
    return mapping

'''most replies to emails. maps and reduces results twice: once to map by threadid, and
then a second time to pick the person who started the email thread and then add the number
of emails within the thread to their total'''
def stat_mostRepliedTo(pool,emaildb):
    partition = list(partitionfunc(emaildb))
    mappings = pool.map(stat_mostRepliedTo_mapfunc, partition)
    results = reducefunc(mappings)

    partition2 = list(partitionfunc(results))
    mappings2 = pool.map(stat_mostRepliedTo_mapfunc2,partition2)
    results2 = reducefunc(mappings2)        
    return sorted(results2, key=lambda obj : (-obj[1],obj[0]))

def stat_mostRepliedTo_mapfunc(objs):
    mapping = {}
    for obj in objs:
        emailstr = re.search(EMAIL_PATTERN,obj["from"]).group(0)
        parsedDate = email.utils.parsedate_tz(obj["date"])
        timestamp = time.mktime(parsedDate[:-1])+parsedDate[-1]
        try:
            mapping[obj["threadid"]].append((emailstr, timestamp))
        except KeyError:
            mapping[obj["threadid"]] = [(emailstr, timestamp)]
    return mapping
def stat_mostRepliedTo_mapfunc2(objs):
    mapping = {}
    for obj in objs:
        #sort thread groups based on timestamp to get the first email
        sortedThreadEmails = sorted(obj[1], key=lambda obj: obj[1])
        try: 
            mapping[sortedThreadEmails[0][0]] += len(sortedThreadEmails) - 1
        except KeyError:
            mapping[sortedThreadEmails[0][0]] = len(sortedThreadEmails) - 1
    return mapping
        

'''most average number of messages per thread
use exponential score to more heavily weight higher numbers 
(ie. responding a bunch to one thread is much worse than replying only once or twice)'''
def stat_mostThreads(pool,emaildb):    
    partition = list(partitionfunc(emaildb))
    mappings = pool.map(stat_mostThreads_mapfunc, partition)
    results = reducefunc(mappings)
    averagedOutput = {}
    for obj in results:
        try:
            averagedOutput[obj[0][1]].append(math.exp(obj[1]))
        except KeyError:
            averagedOutput[obj[0][1]] = [math.exp(obj[1])]
    for k in averagedOutput:
        averagedOutput[k] = sum(averagedOutput[k])/len(averagedOutput[k])
    return sorted(averagedOutput.items(), key=lambda obj : (-obj[1],obj[0]))
def stat_mostThreads_mapfunc(objs):
    mapping = {}
    for obj in objs:
        email = re.search(EMAIL_PATTERN,obj["from"]).group(0)
        try:
            mapping[(obj["threadid"],email)] +=1
        except KeyError:
            mapping[(obj["threadid"],email)] = 1
    return mapping
            
'''calculates the total Fleisch-Kincaid grade level score level of each email's content (this is
later divided by the user's total number of emails to find the avg reading level'''
def stat_readingDifficulty(pool, emaildb):
    partition = list(partitionfunc(emaildb))
    mappings = pool.map(stat_readingDifficulty_mapfunc, partition)
    results = reducefunc(mappings)
    return sorted(results, key=lambda obj : (-obj[1],obj[0]))

'''syllable counter first tries counting syllables based on the cmudict corpus
and then falls back to an imperfect version based on a package in perl'''
d = cmudict.dict()
def countSyllables(word):
    if word in d:
        #taken from https://groups.google.com/d/msg/nltk-users/mCOh_u7V8_I/HsBNcLYM54EJ
        return max([len([y for y in x if isdigit(y[-1])]) for x in d[word]])
    else:
        return syllable.syllable(word)

def stat_readingDifficulty_mapfunc(objs):
    mapping = {}
    for obj in objs:
        email = re.search(EMAIL_PATTERN,obj["from"]).group(0)
        #calculate reading score
        content = ""
        if len(obj["content"]) > 0:
            content = obj["content"][0]
        else:
            continue
        #remove quoted text using regex
        #regex modified from https://github.com/Trindaz/EFZP/blob/master/EFZP.py
        pattern = '(?P<reply_text>On ([a-zA-Z0-9, :/<>@\\."\\[\\]]* wrote:?.*)|From: [\\w@ \\.]* \\[mailto:[\\w\\.]*@[\\w\\.]*\\].*|From: [\\w@ \\.]*(\n|\r\n)+Sent: [\\*\\w@ \\.,:/]*(\n|\r\n)+To:.*(\n|\r\n)+.*|[- ]*Forwarded by [\\w@ \\.,:/]*.*|From: [\\w@ \\.<>\\-]*(\n|\r\n)To: [\\w@ \\.<>\\-]*(\n|\r\n)Date: [\\w@ \\.<>\\-:,]*\n.*|From: [\\w@ \\.<>\\-]*(\n|\r\n)To: [\\w@ \\.<>\\-]*(\n|\r\n)Sent: [\\*\\w@ \\.,:/]*(\n|\r\n).*|From: [\\w@ \\.<>\\-]*(\n|\r\n)To: [\\w@ \\.<>\\-]*(\n|\r\n)Subject:.*|(-| )*Original Message(-| )*.*)'
        groups = re.search(pattern, content, re.IGNORECASE + re.DOTALL)
        if not groups is None and "reply_text" in groups.groupdict():
            content = content.replace(groups.groupdict()["reply_text"],"")
        sentences = sent_tokenize(content)
        words = [word for sentence in sentences for word in word_tokenize(sentence)]
        nsyllables = sum([countSyllables(word) for word in words])
        #calculate Readability Index score
        score = min(20,0.39*(len(words)/len(sentences)) + 11.8*(nsyllables/len(words)) - 15.59)
        try:
            mapping[email] += score
        except KeyError:
            mapping[email] = score
    return mapping
        

#generic mapreduce functions
def partitionfunc(objs):
    obj_count = len(objs)
    chunkSize = int(round(obj_count/JOB_PROCESSES + 0.5))
    k = 0 
    while k < obj_count:
        yield objs[k:k+chunkSize]
        k += chunkSize
def reducefunc(mappings):
    results = {}
    for mapping in mappings:
        for obj, value in mapping.iteritems():
            if type(value) is list:
                try:
                    results[obj].extend(value)
                except KeyError:
                    results[obj] = value
            else:
                try:
                    results[obj] += value
                except KeyError:
                    results[obj] = value
    return results.items()

if __name__ == "__main__":
    pool = Pool(processes=JOB_PROCESSES)
    main(pool)
