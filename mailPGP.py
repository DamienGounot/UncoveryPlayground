# SI changement de from ou de to:
# penser à importer les clefs GPG de l'expéditeur ET de l'emetteur avant
# et à les approuver dans la conf gpg

from envelope import Envelope
import argparse

#################################################################################################
class Mail:

    # Configuration
    smtp_usr='xxxxxxxxx@laposte.net'
    smtp_pwd='xxxxxxxxxxxxxxxxxxx'
    smtp_port=587
    smtp_host='smtp.laposte.net'
    smtp_to='xxxxxxx@gmail.com'


    def __init__(self,subject,message,attachment):
        
        if not isinstance(subject, str):
            raise TypeError("Expected string for subject, got '%s' instead" % type(subject))

        if not isinstance(message, str):
            raise TypeError("Expected string for message, got '%s' instead" % type(message))
        
        if not isinstance(attachment, str):
            raise TypeError("Expected string for attachment path, got '%s' instead" % type(attachment))
        
        try:
            with open(attachment):
                pass
        except:
            raise FileNotFoundError("Attachement file not found : %s" %attachment)

        self.subject = subject
        self.message = message
        self.attachment = attachment

    
    def sendmail(self):
        e = (Envelope()
            .subject(self.subject)
            .message(self.message)
            .sender(Mail.smtp_usr)
            .to(Mail.smtp_to)
            .attach(path=self.attachment)
            .encryption())

        e.as_message()
        e.smtp(Mail.smtp_host, Mail.smtp_port, Mail.smtp_usr, Mail.smtp_pwd, "starttls").send()

#################################################################################################


def  main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", help="sujet du mail", default="Message sans titre")
    parser.add_argument("--msg", help="texte du message", default="Message sans contenu")
    parser.add_argument("--attach",help="fichier à joindre en PJ", required=True)

    args = parser.parse_args() 
    


    m = Mail(args.subject,args.msg,args.attach)
    m.sendmail()


if __name__ == "__main__":
    main()
