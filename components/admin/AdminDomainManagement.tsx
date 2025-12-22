import React, { useMemo, useState, useEffect } from 'react';
import Card from '../Card';
import Button from '../ui/Button';
import SearchBar from '../teacher-dashboard/SearchBar';
import Input from '../ui/Input';
import { useToast } from '../ui/Toast';
import { fetchDomains, createDomain, updateDomain, deleteDomain, type DomainRecord } from '../../services/domainService';
import Spinner from '../Spinner';

type ModalMode = 'add' | 'edit';

const AdminDomainManagement: React.FC = () => {
  const { addToast } = useToast();
  const [searchTerm, setSearchTerm] = useState('');
  const [domains, setDomains] = useState<DomainRecord[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<ModalMode>('add');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [formValues, setFormValues] = useState({ organizationName: '', domainEmail: '' });
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadDomains = async () => {
    setIsLoading(true);
    try {
      const backendDomains = await fetchDomains(searchTerm || undefined);
      const records: DomainRecord[] = backendDomains.map(d => ({
        id: d.id,
        organizationName: d.organization_name,
        domainEmail: `@${d.domain}`,
      }));
      setDomains(records);
    } catch (error) {
      console.error('Failed to fetch domains:', error);
      addToast('도메인 목록을 불러오는데 실패했습니다.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDomains();
  }, [searchTerm]);

  const openAddModal = () => {
    setModalMode('add');
    setEditingId(null);
    setFormValues({ organizationName: '', domainEmail: '' });
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (domain: DomainRecord) => {
    setModalMode('edit');
    setEditingId(domain.id);
    setFormValues({ organizationName: domain.organizationName, domainEmail: domain.domainEmail });
    setFormError(null);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setFormError(null);
  };

  const handleSave = async (event: React.FormEvent) => {
    event.preventDefault();
    const organizationName = formValues.organizationName.trim();
    const domainEmail = formValues.domainEmail.trim();

    if (!organizationName || !domainEmail) {
      setFormError('조직명과 도메인 이메일을 모두 입력해주세요.');
      return;
    }

    if (!domainEmail.startsWith('@')) {
      setFormError('도메인 이메일은 @로 시작해야 합니다.');
      return;
    }

    const domain = domainEmail.slice(1); // remove @

    try {
      if (modalMode === 'add') {
        await createDomain({ domain, organization_name: organizationName });
        addToast('도메인이 추가되었습니다.', 'success');
      } else if (editingId) {
        await updateDomain(editingId, { domain, organization_name: organizationName });
        addToast('도메인이 수정되었습니다.', 'success');
      }
      loadDomains();
      closeModal();
    } catch (error) {
      console.error('Failed to save domain:', error);
      setFormError('저장 실패했습니다.');
    }
  };

  const openDeleteModal = (domainId: number) => {
    setDeletingId(domainId);
    setIsDeleteOpen(true);
  };

  const closeDeleteModal = () => {
    setDeletingId(null);
    setIsDeleteOpen(false);
  };

  const confirmDelete = async () => {
    if (!deletingId) return;
    try {
      await deleteDomain(deletingId);
      addToast('도메인이 삭제되었습니다.', 'success');
      loadDomains();
      closeDeleteModal();
    } catch (error) {
      console.error('Failed to delete domain:', error);
      addToast('도메인 삭제에 실패했습니다.', 'error');
    }
  };

  const deletingDomain = domains.find((item) => item.id === deletingId);
  const isEmpty = domains.length === 0;

  return (
    <div className="space-y-8 mx-auto animate-fadeIn">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-slate-900">도메인 관리</h1>
        <p className="text-sm text-slate-600">업무용 이메일 도메인만 허용됩니다. 예: @company.com</p>
      </div>

      <Card className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="w-full sm:max-w-md">
            <SearchBar
              value={searchTerm}
              onChange={setSearchTerm}
              placeholder="조직명 또는 도메인으로 검색"
            />
          </div>
          <Button type="button" onClick={openAddModal}>
            도메인 추가
          </Button>
        </div>

        {isLoading ? (
          <Spinner label="불러오는 중..." />
        ) : isEmpty ? (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-10 text-center space-y-2">
            <p className="text-slate-700 font-semibold">등록된 도메인이 없습니다.</p>
            <p className="text-sm text-slate-500">도메인을 추가하면 업무용 이메일만 허용됩니다.</p>
            <Button type="button" variant="secondary" onClick={openAddModal} className="mt-2">
              도메인 추가
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-700">
              <thead>
                <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                  <th scope="col" className="px-4 py-3">조직명</th>
                  <th scope="col" className="px-4 py-3">도메인 이메일</th>
                  <th scope="col" className="px-4 py-3 text-right">작업</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {domains.map((domain) => (
                  <tr key={domain.id} className="hover:bg-slate-50/70">
                    <td className="px-4 py-3 font-semibold text-slate-800">{domain.organizationName}</td>
                    <td className="px-4 py-3 text-black">{domain.domainEmail}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => openEditModal(domain)}
                          className="text-sm font-semibold text-primary hover:text-primary-dark"
                        >
                          수정
                        </button>
                        <button
                          type="button"
                          onClick={() => openDeleteModal(domain.id)}
                          className="text-sm font-semibold text-rose-500 hover:text-rose-600"
                        >
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm px-4">
          <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl border border-white/70 p-6 space-y-4 animate-softFadeUp">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold text-primary uppercase tracking-[0.2em]">관리자</p>
                <h3 className="text-xl font-bold text-slate-900 mt-1">
                  {modalMode === 'add' ? '도메인 추가' : '도메인 수정'}
                </h3>
              </div>
              <button
                type="button"
                onClick={closeModal}
                className="text-slate-400 hover:text-slate-700 text-lg font-bold"
                aria-label="닫기"
              >
                x
              </button>
            </div>

            <form className="space-y-3" onSubmit={handleSave}>
              <Input
                label="조직명"
                value={formValues.organizationName}
                onChange={(event) => setFormValues((prev) => ({ ...prev, organizationName: event.target.value }))}
                placeholder="예: Iksan University"
                required
              />
              <Input
                label="도메인 이메일"
                value={formValues.domainEmail}
                onChange={(event) => setFormValues((prev) => ({ ...prev, domainEmail: event.target.value }))}
                placeholder="예: @company.com"
                required
              />
              <p className="text-xs text-slate-500">도메인은 @로 시작해야 합니다.</p>
              {formError && <p className="text-sm text-rose-600 font-semibold">{formError}</p>}
              <div className="flex flex-wrap justify-end gap-2">
                <Button type="button" variant="secondary" onClick={closeModal}>
                  취소
                </Button>
                <Button type="submit">
                  {modalMode === 'add' ? '저장' : '변경사항 저장'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isDeleteOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm px-4">
          <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl border border-white/70 p-6 space-y-4 animate-softFadeUp">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-bold text-slate-900">도메인 삭제</h3>
              <button
                type="button"
                onClick={closeDeleteModal}
                className="text-slate-400 hover:text-slate-700 text-lg font-bold"
                aria-label="닫기"
              >
                x
              </button>
            </div>
            <p className="text-sm text-slate-600">
              정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </p>
            {deletingDomain && (
              <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                대상: <span className="font-semibold">{deletingDomain.domainEmail}</span>
              </div>
            )}
            <div className="flex flex-wrap justify-end gap-2">
              <Button type="button" variant="secondary" onClick={closeDeleteModal}>
                취소
              </Button>
              <Button type="button" variant="danger" onClick={confirmDelete}>
                삭제
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDomainManagement;
