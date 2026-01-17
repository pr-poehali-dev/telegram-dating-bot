import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';
import { Separator } from '@/components/ui/separator';

const API_URL = 'https://functions.poehali.dev/97a00bcd-2455-44bf-90df-b81b9c39e53f';

type Profile = {
  id: number;
  telegram_id: number;
  username: string;
  name: string;
  age: number;
  city: string;
  gender: 'male' | 'female';
  photo_url: string;
  bio?: string;
  created_at: string;
};

type Report = {
  id: number;
  reporter_id: number;
  reported_user_id: number;
  reason: string;
  status: string;
  created_at: string;
  reporter_name: string;
  reported_name: string;
  reported_telegram_id: number;
};

type Stats = {
  total_profiles: number;
  approved: number;
  pending: number;
  rejected: number;
  matches: number;
  pending_reports: number;
  likes_today: number;
};

const Index = () => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('profiles');
  
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profilesRes, reportsRes, statsRes] = await Promise.all([
        fetch(`${API_URL}?action=pending_profiles`),
        fetch(`${API_URL}?action=reports`),
        fetch(`${API_URL}?action=stats`)
      ]);

      const profilesData = await profilesRes.json();
      const reportsData = await reportsRes.json();
      const statsData = await statsRes.json();

      setProfiles(profilesData.profiles || []);
      setReports(reportsData.reports || []);
      setStats(statsData);
    } catch (error) {
      toast({
        title: 'Ошибка загрузки',
        description: 'Не удалось загрузить данные',
        variant: 'destructive'
      });
    }
    setLoading(false);
  };

  const approveProfile = async (profileId: number) => {
    try {
      const response = await fetch(`${API_URL}?action=approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_id: profileId })
      });

      const data = await response.json();
      
      if (data.success) {
        toast({
          title: 'Анкета одобрена',
          description: 'Пользователь может начать пользоваться ботом'
        });
        setProfiles(profiles.filter(p => p.id !== profileId));
        loadData();
      }
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось одобрить анкету',
        variant: 'destructive'
      });
    }
  };

  const rejectProfile = async (profileId: number) => {
    try {
      const response = await fetch(`${API_URL}?action=reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_id: profileId })
      });

      const data = await response.json();
      
      if (data.success) {
        toast({
          title: 'Анкета отклонена',
          description: 'Пользователь получит уведомление'
        });
        setProfiles(profiles.filter(p => p.id !== profileId));
        loadData();
      }
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось отклонить анкету',
        variant: 'destructive'
      });
    }
  };

  const resolveReport = async (reportId: number) => {
    try {
      const response = await fetch(`${API_URL}?action=resolve_report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_id: reportId })
      });

      const data = await response.json();
      
      if (data.success) {
        toast({
          title: 'Жалоба обработана',
          description: 'Статус изменён на "Решено"'
        });
        setReports(reports.filter(r => r.id !== reportId));
        loadData();
      }
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось обработать жалобу',
        variant: 'destructive'
      });
    }
  };

  const dismissReport = async (reportId: number) => {
    try {
      const response = await fetch(`${API_URL}?action=dismiss_report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_id: reportId })
      });

      const data = await response.json();
      
      if (data.success) {
        toast({
          title: 'Жалоба отклонена',
          description: 'Нарушений не обнаружено'
        });
        setReports(reports.filter(r => r.id !== reportId));
        loadData();
      }
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось отклонить жалобу',
        variant: 'destructive'
      });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
                <Icon name="Shield" size={24} className="text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Панель модератора</h1>
                <p className="text-sm text-muted-foreground">Telegram Dating Bot</p>
              </div>
            </div>
            
            <Button variant="outline" size="sm" onClick={loadData} disabled={loading}>
              <Icon name="RefreshCw" size={16} className="mr-2" />
              Обновить
            </Button>
          </div>
        </div>
      </div>

      {stats && (
        <div className="border-b bg-muted/30">
          <div className="container mx-auto px-4 py-6">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
              <Card className="p-4">
                <div className="text-2xl font-bold">{stats.total_profiles}</div>
                <div className="text-sm text-muted-foreground">Всего анкет</div>
              </Card>
              
              <Card className="p-4">
                <div className="text-2xl font-bold text-green-600">{stats.approved}</div>
                <div className="text-sm text-muted-foreground">Одобрено</div>
              </Card>
              
              <Card className="p-4 border-primary">
                <div className="text-2xl font-bold text-primary">{stats.pending}</div>
                <div className="text-sm text-muted-foreground">На модерации</div>
              </Card>
              
              <Card className="p-4">
                <div className="text-2xl font-bold text-red-600">{stats.rejected}</div>
                <div className="text-sm text-muted-foreground">Отклонено</div>
              </Card>
              
              <Card className="p-4">
                <div className="text-2xl font-bold text-purple-600">{stats.matches}</div>
                <div className="text-sm text-muted-foreground">Совпадений</div>
              </Card>
              
              <Card className="p-4 border-orange-500">
                <div className="text-2xl font-bold text-orange-600">{stats.pending_reports}</div>
                <div className="text-sm text-muted-foreground">Жалоб</div>
              </Card>
              
              <Card className="p-4">
                <div className="text-2xl font-bold">{stats.likes_today}</div>
                <div className="text-sm text-muted-foreground">Лайков сегодня</div>
              </Card>
            </div>
          </div>
        </div>
      )}

      <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="profiles" className="gap-2">
              <Icon name="UserCheck" size={16} />
              Анкеты ({profiles.length})
            </TabsTrigger>
            <TabsTrigger value="reports" className="gap-2">
              <Icon name="Flag" size={16} />
              Жалобы ({reports.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profiles" className="mt-6">
            {loading ? (
              <div className="text-center py-12 text-muted-foreground">
                Загрузка...
              </div>
            ) : profiles.length === 0 ? (
              <Card className="p-12 text-center">
                <Icon name="CheckCircle" size={48} className="mx-auto mb-4 text-green-500" />
                <h3 className="text-lg font-semibold mb-2">Нет анкет на модерации</h3>
                <p className="text-muted-foreground">Все анкеты проверены!</p>
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {profiles.map((profile) => (
                  <Card key={profile.id} className="border-2">
                    <div className="aspect-square bg-muted relative overflow-hidden">
                      <img 
                        src={profile.photo_url} 
                        alt={profile.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    
                    <div className="p-4 space-y-3">
                      <div>
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-bold text-lg">{profile.name}, {profile.age}</h3>
                          <Badge variant="secondary">
                            {profile.gender === 'male' ? 'М' : 'Ж'}
                          </Badge>
                        </div>
                        
                        <p className="text-sm text-muted-foreground flex items-center gap-1">
                          <Icon name="MapPin" size={14} />
                          {profile.city}
                        </p>
                        
                        {profile.bio && (
                          <p className="text-sm mt-2">{profile.bio}</p>
                        )}
                      </div>
                      
                      <Separator />
                      
                      <div className="text-xs text-muted-foreground space-y-1">
                        <div className="flex items-center gap-2">
                          <Icon name="User" size={12} />
                          <span>@{profile.username || 'нет username'}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Icon name="Hash" size={12} />
                          <span>ID: {profile.telegram_id}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Icon name="Clock" size={12} />
                          <span>{new Date(profile.created_at).toLocaleString('ru')}</span>
                        </div>
                      </div>
                      
                      <div className="flex gap-2 pt-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="flex-1"
                          onClick={() => rejectProfile(profile.id)}
                        >
                          <Icon name="X" size={16} className="mr-1" />
                          Отклонить
                        </Button>
                        
                        <Button 
                          size="sm"
                          className="flex-1"
                          onClick={() => approveProfile(profile.id)}
                        >
                          <Icon name="Check" size={16} className="mr-1" />
                          Одобрить
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="reports" className="mt-6">
            {loading ? (
              <div className="text-center py-12 text-muted-foreground">
                Загрузка...
              </div>
            ) : reports.length === 0 ? (
              <Card className="p-12 text-center">
                <Icon name="CheckCircle" size={48} className="mx-auto mb-4 text-green-500" />
                <h3 className="text-lg font-semibold mb-2">Нет активных жалоб</h3>
                <p className="text-muted-foreground">Отличная работа!</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {reports.map((report) => (
                  <Card key={report.id} className="p-6 border-2">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center flex-shrink-0">
                        <Icon name="Flag" size={24} className="text-orange-600" />
                      </div>
                      
                      <div className="flex-1 space-y-3">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-bold">Жалоба #{report.id}</h3>
                            <Badge variant="secondary">
                              {new Date(report.created_at).toLocaleDateString('ru')}
                            </Badge>
                          </div>
                          
                          <div className="text-sm space-y-1">
                            <p>
                              <span className="text-muted-foreground">Отправитель:</span>{' '}
                              <span className="font-medium">{report.reporter_name}</span>
                              <span className="text-muted-foreground"> (ID: {report.reporter_id})</span>
                            </p>
                            <p>
                              <span className="text-muted-foreground">Нарушитель:</span>{' '}
                              <span className="font-medium">{report.reported_name}</span>
                              <span className="text-muted-foreground"> (ID: {report.reported_telegram_id})</span>
                            </p>
                          </div>
                          
                          {report.reason && (
                            <div className="mt-2 p-3 bg-muted rounded-md">
                              <p className="text-sm">{report.reason}</p>
                            </div>
                          )}
                        </div>
                        
                        <div className="flex gap-2">
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => dismissReport(report.id)}
                          >
                            <Icon name="X" size={16} className="mr-1" />
                            Отклонить
                          </Button>
                          
                          <Button 
                            size="sm"
                            onClick={() => resolveReport(report.id)}
                          >
                            <Icon name="Check" size={16} className="mr-1" />
                            Принять меры
                          </Button>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
