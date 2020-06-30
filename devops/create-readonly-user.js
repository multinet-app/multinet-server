const users = require('@arangodb/users');

if (!users.exists('readonly')) {
    users.save('readonly', '{{ arango_readonly_password }}');
}

users.grantDatabase('readonly', '*', 'ro');
