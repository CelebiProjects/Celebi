Importing runner credentials
===========================

Import a local Kerberos keytab into Yuki, then bind its name to a runner:

.. code-block:: bash

   celebi-cli add-secret cern-keytab --file ~/.cern.keytab --type kerberos --principal USER@CERN.CH
   celebi-cli update-runner cern --secret cern-keytab

``cern-keytab`` is a user-chosen name. The keytab is uploaded as binary data;
neither its contents nor the local path are added to the project or impressions.
Duplicate names are rejected. This first version supports Kerberos keytabs only.
Both Celebi and Yuki need this implementation; reload Yuki after updating.

Yuki stores credentials in ``Secrets/`` beside its server ``config.json`` with
directory mode 0700 and file mode 0600. This is filesystem-protected storage,
not encryption at rest. No API exposes credential contents. These endpoints
use Yuki's existing deployment access controls; they do not add user login.
Restrict access to the service to trusted clients. The CLI accepts HTTPS or
localhost HTTP (including an SSH tunnel) and refuses HTTP redirects.

Binding is a separate operation from editing runner connection settings and
automatically enables Kerberos. Supported destinations:

* REANA: uploads ``yuki-NAME.keytab``, ``CERN_USER``, and ``CERN_KEYTAB`` using
  REANA's secrets API. CERN user principals are required. REANA secrets are
  account-wide, not workflow-specific. Existing remote names are not overwritten;
  resolve a conflict in REANA before binding. A timeout can leave remote secrets
  present without a local binding; inspect REANA before retrying.
* SSH: copies the keytab over SFTP into a private ``~/.yuki-secret.*`` directory
  outside workflow/cache storage. Existing workflow ticket renewal uses that
  path and principal. The runner copy persists; rebinding does not delete older
  copies. IHEP batch workers and native workflow credential injection are not
  supported by this command yet.

Yuki EOS downloads also use the source REANA runner's bound credential to acquire
a private ticket for each download. Without a binding, existing environment-based
credential configuration continues to work. No actual credential is imported by
installing or testing this feature.
