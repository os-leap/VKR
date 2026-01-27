/**
 * Определение ролей пользователей и их прав
 */

const roles = {
  admin: {
    name: 'Администратор',
    permissions: {
      // Полный доступ ко всему
      canViewAll: true,
      canEditAll: true,
      canDeleteAll: true,
      canCreate: true,
      canViewLogs: true,
      canEditFilters: true,
      canUpdateMethodicalData: true,
      canManageUsers: true,
      canAccessAdminPanel: true
    }
  },
  
  editor: {
    name: 'Редактор',
    permissions: {
      // Может редактировать или удалять любые записи и создавать свои
      canViewAll: true,
      canEditAll: true,
      canDeleteAll: true,
      canCreate: true,
      
      // Не может просматривать логи
      canViewLogs: false,
      
      // Не может редактировать фильтры
      canEditFilters: false,
      
      // Имеет права обновлять методические данные
      canUpdateMethodicalData: true,
      
      // Остальные ограничения
      canManageUsers: false,
      canAccessAdminPanel: false
    }
  },
  
  user: {
    name: 'Пользователь',
    permissions: {
      // Может создавать и просматривать любые записи
      canViewAll: true,
      canCreate: true,
      
      // Но не может редактировать или удалять чужие записи
      canEditAll: false,
      canDeleteAll: false,
      
      // Также не может просматривать логи, редактировать фильтры и т.д.
      canViewLogs: false,
      canEditFilters: false,
      canUpdateMethodicalData: false,
      canManageUsers: false,
      canAccessAdminPanel: false
    }
  }
};

module.exports = roles;