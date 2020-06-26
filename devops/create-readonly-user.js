const users = require('@arangodb/users');

if (!users.exists('{{ arango_readonly_username }}')) {
    users.save('{{ arango_readonly_username }}', '{{ arango_readonly_password }}');
}

users.grantDatabase('{{ arango_readonly_username }}', '*', 'ro');
