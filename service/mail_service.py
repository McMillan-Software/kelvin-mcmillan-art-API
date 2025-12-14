import boto3
from botocore.exceptions import ClientError

ses_client = boto3.client("ses", region_name="ap-southeast-2")  
# Change if your SES region is different

def send_contact_email(name: str, email: str, body: str):
    subject = f"New Contact Inquiry from {name}"
    html_body = f"""
    <h3>New inquiry from {name}</h3>
    <p><b>Email:</b> {email}</p>
    <p><b>Message:</b></p>
    <p>{body}</p>
    """

    try:
        response = ses_client.send_email(
            Source="kelvinmcmillanart@xtra.co.nz",   
            Destination={"ToAddresses": ["kelvinmcmillanart@xtra.co.nz"]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Html": {"Data": html_body},
                    "Text": {"Data": f"{name}\n{email}\n\n{body}"},
                },
            },
        )
        return response

    except ClientError as e:
        print(e.response["Error"]["Message"])
        return None