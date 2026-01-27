/**
 * Пример использования ролей пользователей
 */

const roles = require('./roles');

/**
 * Функция для проверки прав пользователя
 * @param {string} role - Роль пользователя (admin, editor, user)
 * @param {string} permission - Право, которое нужно проверить
 * @returns {boolean} - Имеет ли пользователь указанное право
 */
function checkPermission(role, permission) {
  if (!roles[role]) {
    console.error(`Неизвестная роль: ${role}`);
    return false;
  }

  if (typeof roles[role].permissions[permission] === 'undefined') {
    console.error(`Неизвестное право: ${permission}`);
    return false;
  }

  return roles[role].permissions[permission];
}

/**
 * Функция для получения всех прав пользователя
 * @param {string} role - Роль пользователя
 * @returns {object} - Объект с правами пользователя
 */
function getUserPermissions(role) {
  if (!roles[role]) {
    console.error(`Неизвестная роль: ${role}`);
    return {};
  }

  return roles[role].permissions;
}

// Примеры использования
console.log('Права администратора:', getUserPermissions('admin'));
console.log('Права редактора:', getUserPermissions('editor'));
console.log('Права пользователя:', getUserPermissions('user'));

// Проверка конкретных прав
console.log('\nПроверка прав:');
console.log('Администратор может просматривать логи:', checkPermission('admin', 'canViewLogs'));
console.log('Редактор может просматривать логи:', checkPermission('editor', 'canViewLogs'));
console.log('Пользователь может редактировать все записи:', checkPermission('user', 'canEditAll'));
console.log('Редактор может обновлять методические данные:', checkPermission('editor', 'canUpdateMethodicalData'));

module.exports = {
  checkPermission,
  getUserPermissions
};