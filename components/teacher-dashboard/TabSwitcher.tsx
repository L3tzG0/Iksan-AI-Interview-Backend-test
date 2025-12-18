import type { FC } from 'react';
import type { TabSwitcherProps } from '../../types/teacherDashboard';

const TabSwitcher: FC<TabSwitcherProps> = ({ activeTab, onChange }) => (
  <div className="flex items-center gap-3 pb-3 border-slate-100 border-b">
    {[{ key: 'completed', label: '완료 학생' }, { key: 'manage', label: '학생 관리' }].map((tab) => (
      <button
        key={tab.key}
        type="button"
        onClick={() => onChange(tab.key as TabSwitcherProps['activeTab'])}
        className={`px-3 py-2 text-sm font-semibold rounded-full transition-colors ${
          activeTab === tab.key ? 'bg-primary text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
        }`}
      >
        {tab.label}
      </button>
    ))}
  </div>
);

export default TabSwitcher;
