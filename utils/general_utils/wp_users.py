from lib import wp_cli

def add_admin_user(server, app):
    raise NotImplementedError
    php = """
    	$login = 'myacct1';
    	$passw = 'mypass1';
    	$email = 'myacct1@mydomain.com';

    	if ( !username_exists( $login )  && !email_exists( $email ) ) {
    		$user_id = wp_create_user( $login, $passw, $email );
    		$user = new WP_User( $user_id );
    		$user->set_role( 'administrator' );
    	}
    """
def change_password(server, app, username, password):
    """Changes a user's password.
    The email address can be used in place of the username """
    print("If you happen to need to change the password back, you can go into the database and change the password hash back to {}".format(get_password_hash(server, app, username)))
    wp_cli.run(server, app, "wp user update {} --user_pass={}".format(username, password))

def get_password_hash(server, app, username):
    php = username.replace('"', '\\"')
    php = "'echo get_user_by('slug', {})->data->user_pass;'".format(username)
    return wp_cli.run(server, app, 'eval ' + php)
