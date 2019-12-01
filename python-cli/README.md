# ADFS Token Getter
* * *
1. ## Requirements

    Install python3

    <https://www.python.org/download/releases/3.0/>

2. ## Installation

    * Clone this repository
        ```
        git clone https://git-codecommit.eu-west-1.amazonaws.com/v1/repos/gdc-pcs-adfs-cli-token
        ```

        Install other requrements
        ```
        pip install -r C:\<path to>\gdc-pcs-adfs-cli-token\requirements.txt
        ```
    
    * Depending on the terminal you use either create an alias or a windows batch file.

        **alias**
        ```
        get_aws_creds=python "C:\<path to>\gdc-pcs-adfs-cli-token\get_adfs_token.py"
        ```
        **Batch file**

        *get_aws_creds.bat*
        ```
        @echo off
        python "C:\<path to>\gdc-pcs-adfs-cli-token\get_adfs_token.py"
        ```

2. ## Usage

    ```
    λ get_aws_creds
    
    Vodafone Email:
    email.id@vodafone.com
    Password:
    
    ----------------------------------------------------------------
    Your new access key pair has been stored in the AWS configuration file C:\<path to home>\.aws\credentials under the default profile.
    Note that it will expire at 2018-08-14 08:50:25+00:00.
    After this time you may safely rerun this script to refresh your access key pair.
    ----------------------------------------------------------------
    
    λ 
    ```

    The tokens generated are valid for 1 hour

3. ## References

    <https://aws.amazon.com/blogs/security/how-to-implement-a-general-solution-for-federated-apicli-access-using-saml-2-0/>
